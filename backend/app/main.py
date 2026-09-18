import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import engine, Base, SessionLocal, migrate_sqlite_schema
from app.models import User, FAQ, Notice
from app.utils.security import get_password_hash
from app.routes import (
    auth_router,
    chat_router,
    documents_router,
    faqs_router,
    notices_router,
    logs_router,
    audit_router
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)
migrate_sqlite_schema()

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready Institutional AI Chatbot API for K.K. Wagh Polytechnic, Nashik.",
    version="2.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# Security Headers & Request Tracing Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    # Inject Security Headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Setup CORS Middleware
origins = settings.cors_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(faqs_router)
app.include_router(notices_router)
app.include_router(logs_router)
app.include_router(audit_router)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing K.K. Wagh Polytechnic Chatbot Backend v2.0...")
    db = SessionLocal()
    try:
        # Seed or sync Default Admin User
        admin = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            logger.info(f"Seeding default admin user: {settings.DEFAULT_ADMIN_USERNAME}")
            new_admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True
            )
            db.add(new_admin)
            db.commit()
        else:
            logger.info(f"Syncing password hash for admin user: {settings.DEFAULT_ADMIN_USERNAME}")
            admin.hashed_password = get_password_hash(settings.DEFAULT_ADMIN_PASSWORD)
            admin.is_active = True
            db.commit()

        # Seed sample FAQ if empty
        if db.query(FAQ).count() == 0:
            sample_faq = FAQ(
                question="What are the college working hours of K.K. Wagh Polytechnic?",
                answer="K.K. Wagh Polytechnic working hours are Monday to Saturday from 9:30 AM to 5:15 PM.",
                category="Timings",
                is_active=True
            )
            db.add(sample_faq)
            db.commit()

        # Seed sample Notice if empty
        if db.query(Notice).count() == 0:
            sample_notice = Notice(
                title="Admission Open for First Year Polytechnic 2026-27",
                content="Applications are invited for First Year Diploma engineering courses in Computer, Mechanical, Civil, and Electrical Engineering.",
                category="Admission",
                is_active=True
            )
            db.add(sample_notice)
            db.commit()

    except Exception as e:
        logger.error(f"Error during startup database seed: {str(e)}")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "institute": "K.K. Wagh Polytechnic, Nashik",
        "version": "2.0.0"
    }

@app.get("/api/health")
def health_check():
    """
    Comprehensive health check for SQL Database, Vector DB, and Embedding Service.
    """
    db_status = "healthy"
    chroma_status = "healthy"

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        from app.services.chroma_service import chroma_service
        chroma_service.collection.count()
    except Exception as e:
        chroma_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" and chroma_status == "healthy" else "degraded",
        "database": db_status,
        "vector_store": chroma_status,
        "environment": settings.ENVIRONMENT
    }
