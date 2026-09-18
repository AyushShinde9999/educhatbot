import os
import shutil
import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.utils.security import get_admin_user
from app.services.pdf_processor import pdf_processor
from app.services.chroma_service import chroma_service
from app.services.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/documents", tags=["Document Management"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("General"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Atomic Admin PDF Upload Pipeline:
    1. Validate PDF magic bytes and size limit.
    2. Compute SHA-256 hash & check for duplicates.
    3. Process PDF into 600-char chunks before deleting previous version.
    4. Store in ChromaDB vectors.
    5. On error: rollback disk file, ChromaDB, and database record.
    """
    client_ip = request.client.host if request.client else "unknown"
    original_filename = os.path.basename(file.filename or "").strip()
    if not original_filename or not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid PDF filename is required."
        )

    # Read bytes for validation & hashing
    file_bytes = await file.read()
    
    # 1. Validate PDF content & magic bytes
    is_valid, err_msg = pdf_processor.validate_pdf_content(file_bytes)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )

    # 2. SHA-256 Hash check
    file_hash = pdf_processor.compute_file_hash(file_bytes)
    existing_hash_doc = db.query(Document).filter(
        Document.file_hash == file_hash,
        Document.status == "ready"
    ).first()

    if existing_hash_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate content detected! Identical file already exists under title '{existing_hash_doc.title}'."
        )

    # Temporary file storage during processing
    tmp_filename = f"tmp_{uuid.uuid4().hex}_{original_filename}"
    tmp_file_path = os.path.join(UPLOAD_DIR, tmp_filename)
    final_filename = f"{uuid.uuid4().hex}_{original_filename}"
    final_file_path = os.path.join(UPLOAD_DIR, final_filename)

    try:
        with open(tmp_file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write temporary file to disk: {str(e)}"
        )

    file_size = len(file_bytes)

    # Require an explicit delete before replacing a document with the same name.
    existing_doc = db.query(Document).filter(Document.filename == original_filename).first()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this filename already exists. Delete it before uploading a replacement."
        )

    # Create Database Entry with state = processing
    db_doc = Document(
        title=title.strip() or original_filename,
        filename=original_filename,
        file_path=final_file_path,
        category=category.strip(),
        file_size=file_size,
        file_hash=file_hash,
        chunk_count=0,
        status="processing",
        uploaded_by=current_user.username
    )
    
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # 3. Extract text & chunk
    doc_metadata = {
        "document_id": db_doc.id,
        "title": db_doc.title,
        "filename": db_doc.filename,
        "category": db_doc.category
    }

    try:
        chunks = pdf_processor.process_pdf(tmp_file_path, doc_metadata)
        if not chunks:
            raise ValueError("No readable text found in PDF document.")

        # 4. Add new chunks to ChromaDB
        chroma_service.add_chunks(chunks, doc_id=db_doc.id)

        # Move temporary file to final location
        if os.path.exists(final_file_path) and tmp_file_path != final_file_path:
            os.remove(final_file_path)
        shutil.move(tmp_file_path, final_file_path)

        # Update Document record to ready
        db_doc.chunk_count = len(chunks)
        db_doc.status = "ready"
        db_doc.error_message = None
        db.commit()
        db.refresh(db_doc)

        audit_service.log_action(
            db=db,
            actor=current_user.username,
            action="UPLOAD_DOCUMENT",
            target=db_doc.filename,
            ip_address=client_ip,
            details=f"Uploaded '{db_doc.title}' ({len(chunks)} vectors indexed)"
        )

    except Exception as e:
        logger.error(f"Ingestion pipeline failed for document '{original_filename}': {str(e)}")
        
        # ROLLBACK
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

        chroma_service.delete_document_chunks(db_doc.id)

        db_doc.status = "failed"
        db_doc.error_message = str(e)
        db.commit()

        audit_service.log_action(
            db=db,
            actor=current_user.username,
            action="UPLOAD_FAILED",
            target=original_filename,
            ip_address=client_ip,
            details=f"Processing failed: {str(e)}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing PDF. The upload was rolled back."
        )

    return DocumentUploadResponse(
        message="Document uploaded, text extracted, and embeddings indexed successfully.",
        document=db_doc
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: List all uploaded documents with processing status.
    """
    documents = db.query(Document).order_by(Document.upload_date.desc()).all()
    return documents

@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Protected Admin Endpoint: Delete document by ID (purges metadata & ChromaDB vectors).
    """
    client_ip = request.client.host if request.client else "unknown"
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete chunks from ChromaDB
    chroma_service.delete_document_chunks(doc.id)

    # Remove physical file if exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    doc_title = doc.title
    db.delete(doc)
    db.commit()

    audit_service.log_action(
        db=db,
        actor=current_user.username,
        action="DELETE_DOCUMENT",
        target=doc.filename,
        ip_address=client_ip,
        details=f"Deleted document '{doc_title}' and removed ChromaDB vectors."
    )

    return {"message": f"Document '{doc_title}' deleted successfully."}
