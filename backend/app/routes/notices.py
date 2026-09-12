from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.notice import Notice
from app.models.user import User
from app.schemas.notice import NoticeCreate, NoticeUpdate, NoticeResponse
from app.utils.security import get_admin_user

router = APIRouter(prefix="/api/notices", tags=["Notice Management"])

@router.get("", response_model=List[NoticeResponse])
def get_public_notices(db: Session = Depends(get_db)):
    """
    Public Endpoint: Get all active, non-expired notices.
    """
    now = datetime.utcnow()
    notices = db.query(Notice).filter(
        Notice.is_active == True
    ).order_by(Notice.publish_date.desc()).all()

    active_notices = [
        n for n in notices if n.expiry_date is None or n.expiry_date >= now
    ]
    return active_notices

@router.get("/admin/all", response_model=List[NoticeResponse])
def get_all_notices_admin(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Get all notices (including expired & inactive).
    """
    return db.query(Notice).order_by(Notice.publish_date.desc()).all()

@router.post("/admin", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
def create_notice(notice_in: NoticeCreate, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Create a new Notice.
    """
    notice = Notice(
        title=notice_in.title.strip(),
        content=notice_in.content.strip(),
        category=notice_in.category.strip() if notice_in.category else "Notice",
        expiry_date=notice_in.expiry_date,
        is_active=notice_in.is_active if notice_in.is_active is not None else True
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    return notice

@router.put("/admin/{notice_id}", response_model=NoticeResponse)
def update_notice(notice_id: int, notice_in: NoticeUpdate, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Update an existing Notice.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    if notice_in.title is not None:
        notice.title = notice_in.title.strip()
    if notice_in.content is not None:
        notice.content = notice_in.content.strip()
    if notice_in.category is not None:
        notice.category = notice_in.category.strip()
    if notice_in.expiry_date is not None:
        notice.expiry_date = notice_in.expiry_date
    if notice_in.is_active is not None:
        notice.is_active = notice_in.is_active

    db.commit()
    db.refresh(notice)
    return notice

@router.delete("/admin/{notice_id}")
def delete_notice(notice_id: int, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Delete Notice by ID.
    """
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found.")

    db.delete(notice)
    db.commit()
    return {"message": "Notice deleted successfully."}
