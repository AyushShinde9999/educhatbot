from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.database import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True, nullable=False)
    user_query = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    sources_retrieved = Column(Text, nullable=True) # Stored as JSON string
    fallback_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
