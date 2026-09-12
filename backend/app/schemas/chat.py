from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The user question for the chatbot")
    session_id: Optional[str] = Field(default="default_session", description="Unique session identifier for history tracking")

class SourceReference(BaseModel):
    document_name: str
    page_number: Optional[int] = None
    score: Optional[float] = None
    text_snippet: Optional[str] = None
    category: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference] = []
    fallback_used: bool = False
    session_id: str
