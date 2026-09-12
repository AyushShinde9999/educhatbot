from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatLogResponse(BaseModel):
    id: int
    session_id: str
    user_query: str
    bot_response: str
    sources_retrieved: Optional[str] = None
    fallback_used: bool
    created_at: datetime

    class Config:
        from_attributes = True
