"""Children profile management router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from passlib.context import CryptContext

from database import get_db
from models import Parent, Child
from schemas import ChildCreate, ChildResponse

router = APIRouter(prefix="/children", tags=["Children"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
def create_child(child: ChildCreate, parent_id: int, db: Session = Depends(get_db)):
    """Create a new child profile"""
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
        preferred_language=child.preferred_language
    )

    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    return new_child

@router.get("/", response_model=List[ChildResponse])
def get_children(parent_id: int, db: Session = Depends(get_db)):
    """Get all children for a parent"""
    children = db.query(Child).filter(Child.parent_id == parent_id).all()
    return children

@router.get("/{child_id}", response_model=ChildResponse)
def get_child(child_id: int, db: Session = Depends(get_db)):
    """Get a specific child"""
    child = db.query(Child).filter(Child.id == child_id).first()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found"
        )

    return child
