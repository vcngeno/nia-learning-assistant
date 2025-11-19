from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from database import get_db
from models import User, Child
from schemas import ParentCreate, ParentLogin, ChildLogin
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings - use same key as auth.py
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/parent/register", status_code=status.HTTP_201_CREATED)
async def register_parent(parent_data: ParentCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists (async query)
    result = await db.execute(
        select(User).where(User.email == parent_data.email)
    )
    existing_parent = result.scalar_one_or_none()

    if existing_parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new parent
    new_parent = User(
        email=parent_data.email,
        password_hash=hash_password(parent_data.password),
        full_name=parent_data.full_name
    )

    db.add(new_parent)
    await db.commit()
    await db.refresh(new_parent)

    return {
        "message": "Parent account created successfully",
        "parent_id": new_parent.id,
        "email": new_parent.email
    }


@router.post("/parent/login")
async def login_parent(login_data: ParentLogin, db: AsyncSession = Depends(get_db)):
    # Find parent by email (async query)
    result = await db.execute(
        select(User).where(User.email == login_data.email)
    )
    parent = result.scalar_one_or_none()

    if not parent or not verify_password(login_data.password, parent.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token with EMAIL in "sub" (matches auth.py expectations)
    access_token = create_access_token(
        data={"sub": parent.email, "type": "parent", "user_id": parent.id}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "parent_id": parent.id,
        "email": parent.email,
        "full_name": parent.full_name
    }


@router.post("/child/login")
async def login_child(login_data: ChildLogin, db: AsyncSession = Depends(get_db)):
    # Find child by username (using first_name) - async query
    result = await db.execute(
        select(Child).where(Child.first_name == login_data.username)
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or PIN"
        )

    # Verify PIN
    if not child.pin_hash or not verify_password(login_data.pin, child.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or PIN"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(child.id),
            "type": "child",
            "parent_id": str(child.parent_id)
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "child_id": child.id,
        "username": child.first_name,
        "display_name": child.nickname or child.first_name,
        "grade_level": child.grade_level
    }
