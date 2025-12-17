"""Children profile management router"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import logging

from database import get_db
from models import Parent, Child
from schemas import ChildCreate, ChildResponse

router = APIRouter(prefix="/children", tags=["Children"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

def get_current_parent_id(authorization: Optional[str] = Header(None)) -> int:
    """Extract parent ID from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        parent_id = int(payload.get("sub"))
        if not parent_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return parent_id
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db),
    parent_id: int = Depends(get_current_parent_id)
):
    """Create a new child profile"""
    logger.info(f"Creating child for parent_id: {parent_id}")
    logger.info(f"Child data: {child.model_dump()}")

    parent = db.query(Parent).filter(Parent.id == parent_id).first()

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent not found"
        )

    hashed_pin = get_password_hash(child.pin)

    new_child = Child(
        parent_id=parent_id,
        first_name=child.first_name,
        nickname=child.nickname,
        date_of_birth=child.date_of_birth,
        grade_level=child.grade_level,
        hashed_pin=hashed_pin,
        preferred_language=child.preferred_language or "en"
    )

    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    logger.info(f"Child created successfully: {new_child.id}")
    return new_child

@router.get("/", response_model=List[ChildResponse])
def get_children(
    db: Session = Depends(get_db),
    parent_id: int = Depends(get_current_parent_id)
):
    """Get all children for authenticated parent"""
    children = db.query(Child).filter(Child.parent_id == parent_id).all()
    return children

@router.get("/{child_id}", response_model=ChildResponse)
def get_child(
    child_id: int,
    db: Session = Depends(get_db),
    parent_id: int = Depends(get_current_parent_id)
):
    """Get a specific child"""
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == parent_id
    ).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )

    return child
