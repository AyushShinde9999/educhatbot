from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class NoticeBase(BaseModel):
    title: str = Field(..., min_length=3)
    content: str = Field(..., min_length=5)
    category: Optional[str] = "Notice"
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = True

class NoticeCreate(NoticeBase):
    pass

class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class NoticeResponse(NoticeBase):
    id: int
    publish_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True
