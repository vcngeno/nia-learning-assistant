#!/bin/bash

echo "🚀 Setting up Nia Backend - Complete Clean Install"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create models.py
echo -e "${BLUE}Creating models.py...${NC}"
cat > models.py << 'EOF'
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class ConsentType(enum.Enum):
    """Types of parental consent"""
    EMAIL_VERIFICATION = "email_verification"
    TERMS_ACCEPTANCE = "terms_acceptance"
    DATA_COLLECTION = "data_collection"
    MONITORING = "monitoring"

class User(Base):
    """Parent/Guardian accounts"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user")

class Child(Base):
    """Child profiles (COPPA compliant)"""
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    first_name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    grade_level = Column(String, nullable=False)
    
    pin_hash = Column(String, nullable=True)
    
    avatar_url = Column(String, nullable=True)
    learning_preferences = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    requires_supervision = Column(Boolean, default=True, nullable=False)
    content_filter_level = Column(String, default="strict", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    parent = relationship("User", back_populates="children")
    conversations = relationship("Conversation", back_populates="child", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="child")

class Session(Base):
    """User session tracking"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="sessions")

class ConsentRecord(Base):
    """COPPA compliance - parental consent tracking"""
    __tablename__ = "consent_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    consent_type = Column(SQLEnum(ConsentType), nullable=False)
    granted = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="consent_records")

class Conversation(Base):
    """Chat conversations"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String, nullable=False)
    folder = Column(String, default="General", nullable=False)
    topics = Column(JSON, nullable=True)
    
    message_count = Column(Integer, default=0, nullable=False)
    total_depth_reached = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    child = relationship("Child", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    model_used = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    sources = Column(JSON, nullable=True)
    
    depth_level = Column(Integer, default=1, nullable=False)
    
    flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")

class UsageLog(Base):
    """Track child usage for analytics"""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    
    session_duration_seconds = Column(Integer, nullable=True)
    messages_sent = Column(Integer, default=0)
    topics_explored = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    child = relationship("Child", back_populates="usage_logs")

class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
EOF

# Create auth.py
echo -e "${BLUE}Creating auth.py...${NC}"
cat > auth.py << 'EOF'
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import logging

from database import get_db
from models import User, Session as DBSession

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class AuthService:
    """Authentication service for user management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"Token decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    
    token = credentials.credentials
    
    try:
        payload = AuthService.decode_token(token)
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user

async def get_current_active_parent(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active parent user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def hash_pin(pin: str) -> str:
    """Hash a PIN for child authentication"""
    return pwd_context.hash(pin)

def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against its hash"""
    return pwd_context.verify(plain_pin, hashed_pin)
EOF

# Create routers/__init__.py
echo -e "${BLUE}Creating routers/__init__.py...${NC}"
cat > routers/__init__.py << 'EOF'
from . import auth, children, conversation, dashboard

__all__ = ["auth", "children", "conversation", "dashboard"]
EOF

# Create services/__init__.py
echo -e "${BLUE}Creating services/__init__.py...${NC}"
cat > services/__init__.py << 'EOF'
from .conversation_service import ConversationService
from .rag_service import RAGService, get_rag_service

__all__ = ["ConversationService", "RAGService", "get_rag_service"]
EOF

echo -e "${GREEN}✅ Core files created!${NC}"
echo -e "${BLUE}Creating router files...${NC}"
