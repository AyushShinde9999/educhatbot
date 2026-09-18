from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    category = Column(String(100), default="General", index=True)
    file_size = Column(Integer, default=0) # in bytes
    file_hash = Column(String(64), index=True, nullable=True) # SHA-256 hash
    chunk_count = Column(Integer, default=0)
    status = Column(String(30), default="ready", index=True) # pending, processing, ready, failed
    error_message = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100), default="admin")
