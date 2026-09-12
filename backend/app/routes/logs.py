from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.chat_log import ChatLog
from app.models.document import Document
from app.models.faq import FAQ
from app.models.notice import Notice
from app.models.user import User
from app.schemas.chat_log import ChatLogResponse
from app.utils.security import get_admin_user

router = APIRouter(prefix="/api/admin/logs", tags=["Chat Logs & Analytics"])

@router.get("", response_model=List[ChatLogResponse])
def get_chat_logs(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Protected Admin Endpoint: Retrieve recent user query logs.
    """
    logs = db.query(ChatLog).order_by(ChatLog.created_at.desc()).limit(limit).all()
    return logs

@router.get("/analytics")
def get_dashboard_analytics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Protected Admin Endpoint: Return counts for documents, FAQs, active notices, and query statistics.
    """
    total_documents = db.query(Document).count()
    total_faqs = db.query(FAQ).count()
    active_faqs = db.query(FAQ).filter(FAQ.is_active == True).count()
    total_notices = db.query(Notice).count()
    active_notices = db.query(Notice).filter(Notice.is_active == True).count()
    
    total_queries = db.query(ChatLog).count()
    fallback_queries = db.query(ChatLog).filter(ChatLog.fallback_used == True).count()
    grounded_queries = total_queries - fallback_queries

    return {
        "total_documents": total_documents,
        "total_faqs": total_faqs,
        "active_faqs": active_faqs,
        "total_notices": total_notices,
        "active_notices": active_notices,
        "total_queries": total_queries,
        "grounded_queries": grounded_queries,
        "fallback_queries": fallback_queries
    }
