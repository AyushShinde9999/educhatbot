from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    category: str
    file_size: int
    chunk_count: int
    status: str = "ready"
    error_message: Optional[str] = None
    file_hash: Optional[str] = None
    upload_date: datetime
    uploaded_by: str

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
