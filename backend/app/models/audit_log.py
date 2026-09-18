from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(100), nullable=False, index=True) # username or 'system' / 'anonymous'
    action = Column(String(100), nullable=False, index=True) # UPLOAD_DOCUMENT, DELETE_DOCUMENT, LOGIN_SUCCESS, etc.
    target = Column(String(255), nullable=True) # Resource target (e.g. document filename, faq id)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
