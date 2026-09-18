from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.faqs import router as faqs_router
from app.routes.notices import router as notices_router
from app.routes.logs import router as logs_router
from app.routes.audit import router as audit_router

__all__ = [
    "auth_router",
    "chat_router",
    "documents_router",
    "faqs_router",
    "notices_router",
    "logs_router",
    "audit_router"
]
