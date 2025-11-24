from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from database import engine, Base
from routers import conversation, auth, children, dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(name)s] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NIA")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🌟 Nia is starting up...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Database tables created successfully")

    # Run migrations for child table
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS preferred_language VARCHAR DEFAULT 'en' NOT NULL"
            ))
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS reading_level VARCHAR DEFAULT 'at grade level'"
            ))
            await conn.execute(text(
                "ALTER TABLE children ADD COLUMN IF NOT EXISTS learning_accommodations TEXT DEFAULT '[]'"
            ))
            logger.info("✅ Migrations applied successfully")
    except Exception as e:
        logger.warning(f"Migration note: {e}")

    logger.info("✅ Nia API started successfully!")

    yield

    logger.info("👋 Nia is shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Nia - AI Learning Assistant",
    description="COPPA-compliant AI tutoring platform for children",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(children.router, prefix="/api/v1/children", tags=["Children"])
app.include_router(conversation.router, prefix="/api/v1/conversation", tags=["Conversation"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Welcome to Nia API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Nia Learning Assistant API",
        "version": "1.0.0"
    }

# Version: 1.0.1 - Added migration support
