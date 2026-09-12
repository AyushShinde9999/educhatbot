import json
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import rag_service
from app.models.chat_log import ChatLog
from app.utils.rate_limiter import chat_rate_limiter

router = APIRouter(prefix="/api/chat", tags=["Chatbot Widget"])

@router.post("", response_model=ChatResponse)
def ask_question(chat_req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    """
    Public Endpoint: Accepts user question and session_id.
    Runs full RAG pipeline (search vector DB & SQL FAQs -> Gemini -> grounded response).
    Logs question and response in database.
    """
    # Apply rate limiting
    chat_rate_limiter.check_rate_limit(request)

    question = chat_req.question.strip()
    session_id = chat_req.session_id or "default_session"

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )

    # Process question through RAG Service
    result = rag_service.generate_answer(question, db)

    # Save to ChatLog table
    try:
        chat_log = ChatLog(
            session_id=session_id,
            user_query=question,
            bot_response=result["answer"],
            sources_retrieved=json.dumps(result["sources"]),
            fallback_used=result["fallback_used"]
        )
        db.add(chat_log)
        db.commit()
    except Exception as e:
        db.rollback()

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        fallback_used=result["fallback_used"],
        session_id=session_id
    )
