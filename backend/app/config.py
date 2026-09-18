import os
from pydantic_settings import BaseSettings
from typing import List, Union

class Settings(BaseSettings):
    APP_NAME: str = "K.K. Wagh Polytechnic AI Chatbot API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./kkwagh.db"
    REDIS_URL: str = "" # Optional: e.g. redis://localhost:6379/0

    GEMINI_API_KEY: str = ""
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    JWT_SECRET_KEY: str = "kk_wagh_secret_jwt_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@kkwagh.edu.in"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@KKWagh2026"

    # Admin Registration Secret Key for protecting /register endpoint
    ADMIN_REGISTRATION_SECRET: str = "kkwagh_admin_reg_secret_2026"

    # Security settings
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    MAX_UPLOAD_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB

    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5500"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            if self.CORS_ORIGINS == "*":
                return ["*"]
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    def validate_production_settings(self):
        if self.is_production:
            if self.JWT_SECRET_KEY == "kk_wagh_secret_jwt_key_2026_change_in_production":
                raise ValueError("SECURITY RISK: Default JWT_SECRET_KEY cannot be used in production!")
            if self.DEFAULT_ADMIN_PASSWORD == "Admin@KKWagh2026":
                raise ValueError("SECURITY RISK: Default DEFAULT_ADMIN_PASSWORD must be changed in production!")
            if self.ADMIN_REGISTRATION_SECRET == "kkwagh_admin_reg_secret_2026":
                raise ValueError("SECURITY RISK: Default ADMIN_REGISTRATION_SECRET must be changed in production!")
            if self.CORS_ORIGINS == "*":
                raise ValueError("SECURITY RISK: Wildcard CORS_ORIGINS '*' is forbidden in production!")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
if settings.is_production:
    settings.validate_production_settings()
