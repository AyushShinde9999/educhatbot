from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FAQBase(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=2)
    category: Optional[str] = "General"
    is_active: Optional[bool] = True

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class FAQResponse(FAQBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
