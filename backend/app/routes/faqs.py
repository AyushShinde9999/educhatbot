from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.faq import FAQ
from app.models.user import User
from app.schemas.faq import FAQCreate, FAQUpdate, FAQResponse
from app.utils.security import get_admin_user

router = APIRouter(prefix="/api/faqs", tags=["FAQ Management"])

@router.get("", response_model=List[FAQResponse])
def get_public_faqs(db: Session = Depends(get_db)):
    """
    Public Endpoint: Get all active FAQs.
    """
    return db.query(FAQ).filter(FAQ.is_active == True).order_by(FAQ.created_at.desc()).all()

@router.get("/admin/all", response_model=List[FAQResponse])
def get_all_faqs_admin(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Get all FAQs (including inactive).
    """
    return db.query(FAQ).order_by(FAQ.created_at.desc()).all()

@router.post("/admin", response_model=FAQResponse, status_code=status.HTTP_201_CREATED)
def create_faq(faq_in: FAQCreate, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Create a new FAQ.
    """
    faq = FAQ(
        question=faq_in.question.strip(),
        answer=faq_in.answer.strip(),
        category=faq_in.category.strip() if faq_in.category else "General",
        is_active=faq_in.is_active if faq_in.is_active is not None else True
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq

@router.put("/admin/{faq_id}", response_model=FAQResponse)
def update_faq(faq_id: int, faq_in: FAQUpdate, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Update an existing FAQ.
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found.")

    if faq_in.question is not None:
        faq.question = faq_in.question.strip()
    if faq_in.answer is not None:
        faq.answer = faq_in.answer.strip()
    if faq_in.category is not None:
        faq.category = faq_in.category.strip()
    if faq_in.is_active is not None:
        faq.is_active = faq_in.is_active

    db.commit()
    db.refresh(faq)
    return faq

@router.delete("/admin/{faq_id}")
def delete_faq(faq_id: int, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Protected Admin Endpoint: Delete FAQ by ID.
    """
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found.")

    db.delete(faq)
    db.commit()
    return {"message": "FAQ deleted successfully."}
