"""Authentication router with JWT tokens"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os

from jose import jwt, JWTError

from database import get_db
from models import Parent, Child
from schemas import ParentCreate, ParentLogin, ChildLogin, Token
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate to 72 bytes for bcrypt compatibility
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    # Truncate to 72 bytes for bcrypt compatibility
    return pwd_context.hash(password[:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/parent/register", response_model=Token)
def register_parent(parent: ParentCreate, db: Session = Depends(get_db)):
    """Register a new parent account"""
    # Check if parent already exists
    existing = db.query(Parent).filter(Parent.email == parent.email).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new parent
    hashed_password = get_password_hash(parent.password)
    new_parent = Parent(
        email=parent.email,
        full_name=parent.full_name,
        hashed_password=hashed_password
    )

    db.add(new_parent)
    db.commit()
    db.refresh(new_parent)

    # Create access token
    access_token = create_access_token(data={"sub": str(new_parent.id), "type": "parent"})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "parent_id": new_parent.id,
        "email": new_parent.email,
        "full_name": new_parent.full_name
    }

@router.post("/parent/login", response_model=Token)
def login_parent(credentials: ParentLogin, db: Session = Depends(get_db)):
    """Login parent account"""
    parent = db.query(Parent).filter(Parent.email == credentials.email).first()

    if not parent or not verify_password(credentials.password, parent.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(data={"sub": str(parent.id), "type": "parent"})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "parent_id": parent.id,
        "email": parent.email,
        "full_name": parent.full_name
    }

@router.post("/child/login", response_model=dict)
def login_child(credentials: ChildLogin, db: Session = Depends(get_db)):
    """Login child with PIN"""
    child = db.query(Child).filter(Child.id == credentials.child_id).first()

    if not child or not verify_password(credentials.pin, child.hashed_pin):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid PIN"
        )

    return {
        "child_id": child.id,
        "first_name": child.first_name,
        "grade_level": child.grade_level
    }
