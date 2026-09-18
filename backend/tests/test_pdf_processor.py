import pytest
from app.services.pdf_processor import pdf_processor

def test_clean_text():
    raw_text = "  Hello \n  World \x00 Extra   Spaces  "
    cleaned = pdf_processor.clean_text(raw_text)
    assert cleaned == "Hello World Extra Spaces"

def test_pdf_magic_bytes_validation():
    # Valid PDF magic header bytes
    valid_pdf_bytes = b"%PDF-1.7 header content here..."
    is_valid, msg = pdf_processor.validate_pdf_content(valid_pdf_bytes)
    assert is_valid is True
    assert msg == "Valid"

    # Invalid non-PDF file bytes
    invalid_bytes = b"<html>Not a PDF</html>"
    is_valid_inv, msg_inv = pdf_processor.validate_pdf_content(invalid_bytes)
    assert is_valid_inv is False
    assert "Invalid PDF content" in msg_inv

def test_chunk_text_overlap():
    text = "A" * 1200 # 1200 characters text
    metadata = {"document_id": 1, "title": "Test Doc", "filename": "test.pdf", "category": "General"}
    
    chunks = pdf_processor.chunk_text(text, page_number=1, doc_metadata=metadata)
    assert len(chunks) >= 2
    assert len(chunks[0]["text"]) == 600
    assert chunks[0]["metadata"]["page_number"] == 1
    assert chunks[0]["metadata"]["document_id"] == 1

def test_compute_file_hash():
    content = b"Sample document bytes for SHA-256"
    hash1 = pdf_processor.compute_file_hash(content)
    hash2 = pdf_processor.compute_file_hash(content)
    assert hash1 == hash2
    assert len(hash1) == 64
