from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/nia_db")
    async_database_url: str = os.getenv("ASYNC_DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5433/nia_db")

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
