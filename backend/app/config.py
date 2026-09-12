import os
from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    APP_NAME: str = "K.K. Wagh Polytechnic AI Chatbot API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./kkwagh.db"

    GEMINI_API_KEY: str = ""
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    JWT_SECRET_KEY: str = "kk_wagh_secret_jwt_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@kkwagh.edu.in"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@KKWagh2026"

    CORS_ORIGINS: Union[str, List[str]] = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS == "*":
                return ["*"]
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
