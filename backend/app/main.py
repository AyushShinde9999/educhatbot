import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, FAQ, Notice
from app.utils.security import get_password_hash
from app.routes import (
    auth_router,
    chat_router,
    documents_router,
    faqs_router,
    notices_router,
    logs_router
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready Institutional AI Chatbot API for K.K. Wagh Polytechnic, Nashik.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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

@app.on_event("startup")
def startup_event():
    logger.info("Initializing K.K. Wagh Polytechnic Chatbot Backend...")
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
            logger.info(f"Updating password hash for existing admin user: {settings.DEFAULT_ADMIN_USERNAME}")
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
        "docs": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }
