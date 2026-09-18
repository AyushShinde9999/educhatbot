from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def migrate_sqlite_schema():
    """Apply small additive migrations needed by existing local SQLite databases."""
    if not db_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    document_columns = {column["name"] for column in inspector.get_columns("documents")}
    missing_columns = {
        "file_hash": "VARCHAR(64)",
        "status": "VARCHAR(30) DEFAULT 'ready'",
        "error_message": "TEXT",
    }
    with engine.begin() as connection:
        for column_name, column_definition in missing_columns.items():
            if column_name not in document_columns:
                connection.execute(
                    text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_definition}")
                )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
