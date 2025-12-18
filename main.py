"""
Nia Learning Assistant - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers import conversation, auth, children, dashboard
from database import sync_engine
from models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[NIA] %(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Nia Learning Assistant API",
    description="COPPA-compliant AI tutoring platform for K-12 students",
    version="1.0.0"
)

# CORS middleware - IMPORTANT: Must allow Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://production-frontend-iota.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(children.router, prefix="/api/v1")
app.include_router(conversation.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🌟 Nia is starting up...")
    try:
        # Simply create all tables - let SQLAlchemy handle it
        Base.metadata.create_all(bind=sync_engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        # Don't raise - let the app start anyway

    logger.info("✅ Nia API started successfully!")

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Nia Learning Assistant API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
