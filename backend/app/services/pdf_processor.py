import fitz  # PyMuPDF
import re
import hashlib
from typing import List, Dict, Any, Tuple
from app.config import settings

class PDFProcessor:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def compute_file_hash(self, file_bytes: bytes) -> str:
        """
        Calculates SHA-256 hash of raw file content.
        """
        return hashlib.sha256(file_bytes).hexdigest()

    def validate_pdf_content(self, file_bytes: bytes) -> Tuple[bool, str]:
        """
        Validates PDF content by checking magic header bytes and size limits.
        """
        if not file_bytes:
            return False, "Uploaded file is empty."

        if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            return False, f"File size exceeds maximum limit of {max_mb} MB."

        # Check PDF Magic Bytes (%PDF-)
        if not file_bytes.startswith(b'%PDF-'):
            return False, "Invalid PDF content. File header does not match standard PDF format."

        return True, "Valid"

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespace and non-printable control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text page by page from a PDF file.
        """
        doc = fitz.open(pdf_path)
        pages_content = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            raw_text = page.get_text("text")
            cleaned = self.clean_text(raw_text)
            if cleaned:
                pages_content.append({
                    "page_number": page_num + 1,
                    "text": cleaned
                })

        doc.close()
        return pages_content

    def chunk_text(self, text: str, page_number: int, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits text into chunks of specified size with overlap.
        """
        chunks = []
        if not text:
            return chunks

        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "document_id": doc_metadata.get("document_id"),
                        "title": doc_metadata.get("title", ""),
                        "filename": doc_metadata.get("filename", ""),
                        "category": doc_metadata.get("category", "General"),
                        "page_number": page_number,
                        "chunk_index": len(chunks)
                    }
                })

            if end == text_len:
                break
            start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def process_pdf(self, pdf_path: str, doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extracts and chunks an entire PDF file.
        """
        pages = self.extract_text_from_pdf(pdf_path)
        all_chunks = []

        for page in pages:
            page_chunks = self.chunk_text(
                text=page["text"],
                page_number=page["page_number"],
                doc_metadata=doc_metadata
            )
            all_chunks.extend(page_chunks)

        return all_chunks

pdf_processor = PDFProcessor(chunk_size=600, chunk_overlap=100)
