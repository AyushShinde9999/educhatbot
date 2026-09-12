import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.utils.security import get_admin_user
from app.services.pdf_processor import pdf_processor
from app.services.chroma_service import chroma_service

router = APIRouter(prefix="/api/admin/documents", tags=["Document Management"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("General"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Protected Admin Endpoint:
    1. Upload PDF document.
    2. Save file locally in uploads/ directory.
    3. Process PDF (extract text, clean, split into 600-char chunks with 100 overlap).
    4. Store chunks and embeddings in ChromaDB.
    5. Save document metadata in database.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported."
        )

    # Save PDF file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    file_size = os.path.getsize(file_path)

    # Check if document already exists with same filename (replace if so)
    existing_doc = db.query(Document).filter(Document.filename == file.filename).first()
    if existing_doc:
        chroma_service.delete_document_chunks(existing_doc.id)
        db.delete(existing_doc)
        db.commit()

    # Create Document record
    db_doc = Document(
        title=title.strip() or file.filename,
        filename=file.filename,
        file_path=file_path,
        category=category.strip(),
        file_size=file_size,
        chunk_count=0,
        uploaded_by=current_user.username
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Extract text and chunk PDF
    doc_metadata = {
        "document_id": db_doc.id,
        "title": db_doc.title,
        "filename": db_doc.filename,
        "category": db_doc.category
    }

    try:
        chunks = pdf_processor.process_pdf(file_path, doc_metadata)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text found in PDF document."
            )

        # Store chunks in ChromaDB
        chroma_service.add_chunks(chunks, doc_id=db_doc.id)

        # Update chunk count
        db_doc.chunk_count = len(chunks)
        db.commit()
        db.refresh(db_doc)

    except Exception as e:
        # Cleanup DB on failure
        db.delete(db_doc)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF and embedding chunks: {str(e)}"
        )

    return DocumentUploadResponse(
        message="Document uploaded, text extracted, and embeddings stored successfully.",
        document=db_doc
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: List all uploaded documents.
    """
    documents = db.query(Document).order_by(Document.upload_date.desc()).all()
    return documents

@router.delete("/{doc_id}")
def delete_document(doc_id: int, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Delete document by ID (purges metadata & ChromaDB vectors).
    """
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

    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.title}' deleted successfully."}
