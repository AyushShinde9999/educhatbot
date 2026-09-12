import fitz  # PyMuPDF
import re
from typing import List, Dict, Any

class PDFProcessor:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespace and linebreaks
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extracts text page by page from a PDF file.
        Returns a list of dicts containing page number and extracted raw text.
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
