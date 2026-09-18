from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.security import get_admin_user

router = APIRouter(prefix="/api/admin/audit-logs", tags=["Audit Logging"])

class AuditLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    target: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Protected Admin Endpoint: Retrieve administrative audit trail.
    """
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
