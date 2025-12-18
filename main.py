"""Nia Learning Assistant API"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from routers import auth, children, conversation, dashboard

logging.basicConfig(level=logging.INFO, format='[NIA] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Nia API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(children.router, prefix="/api/v1")
app.include_router(conversation.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    logger.info("✅ Nia API started")

@app.get("/")
def root():
    return {"status": "healthy"}

@app.get("/health")
def health():
    return {"status": "healthy"}
