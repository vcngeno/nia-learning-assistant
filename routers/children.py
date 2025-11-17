from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date
import logging

from database import get_db
from models import User, Child
from auth import get_current_active_parent, hash_pin, verify_pin

router = APIRouter()
logger = logging.getLogger(__name__)

class ChildCreate(BaseModel):
    first_name: str
    nickname: Optional[str] = None
    date_of_birth: date
    grade_level: str
    pin: str
    
    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit() or len(v) not in [4, 6]:
            raise ValueError('PIN must be 4 or 6 digits')
        return v

class ChildResponse(BaseModel):
    id: int
    first_name: str
    nickname: Optional[str]
    date_of_birth: date
    grade_level: str
    is_active: bool
    created_at: datetime

class PINVerify(BaseModel):
    child_id: int
    pin: str

@router.post("/", response_model=ChildResponse, status_code=201)
async def create_child(child_data: ChildCreate, current_user: User = Depends(get_current_active_parent), db: AsyncSession = Depends(get_db)):
    dob_datetime = datetime.combine(child_data.date_of_birth, datetime.min.time())
    new_child = Child(
        parent_id=current_user.id,
        first_name=child_data.first_name,
        nickname=child_data.nickname,
        date_of_birth=dob_datetime,
        grade_level=child_data.grade_level,
        pin_hash=hash_pin(child_data.pin),
        is_active=True
    )
    db.add(new_child)
    await db.commit()
    await db.refresh(new_child)
    logger.info(f"✅ Child created: {new_child.first_name}")
    return {
        "id": new_child.id,
        "first_name": new_child.first_name,
        "nickname": new_child.nickname,
        "date_of_birth": new_child.date_of_birth.date(),
        "grade_level": new_child.grade_level,
        "is_active": new_child.is_active,
        "created_at": new_child.created_at
    }

@router.get("/", response_model=List[ChildResponse])
async def list_children(current_user: User = Depends(get_current_active_parent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Child).where(Child.parent_id == current_user.id).where(Child.is_active == True))
    children = result.scalars().all()
    return [{"id": c.id, "first_name": c.first_name, "nickname": c.nickname, "date_of_birth": c.date_of_birth.date(), "grade_level": c.grade_level, "is_active": c.is_active, "created_at": c.created_at} for c in children]

@router.post("/verify-pin")
async def verify_child_pin(verify_data: PINVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Child).where(Child.id == verify_data.child_id))
    child = result.scalar_one_or_none()
    if not child or not child.is_active:
        raise HTTPException(status_code=404, detail="Child not found")
    if not verify_pin(verify_data.pin, child.pin_hash):
        raise HTTPException(status_code=401, detail="Incorrect PIN")
    logger.info(f"✅ PIN verified: {child.first_name}")
    return {"verified": True, "child": {"id": child.id, "first_name": child.first_name, "nickname": child.nickname, "grade_level":
# 2. Create routers/children.py
cat > routers/children.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date
import logging

from database import get_db
from models import User, Child
from auth import get_current_active_parent, hash_pin, verify_pin

router = APIRouter()
logger = logging.getLogger(__name__)

class ChildCreate(BaseModel):
    first_name: str
    nickname: Optional[str] = None
    date_of_birth: date
    grade_level: str
    pin: str
    
    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v):
        if not v.isdigit() or len(v) not in [4, 6]:
            raise ValueError('PIN must be 4 or 6 digits')
        return v

class ChildResponse(BaseModel):
    id: int
    first_name: str
    nickname: Optional[str]
    date_of_birth: date
    grade_level: str
    is_active: bool
    created_at: datetime

class PINVerify(BaseModel):
    child_id: int
    pin: str

@router.post("/", response_model=ChildResponse, status_code=201)
async def create_child(child_data: ChildCreate, current_user: User = Depends(get_current_active_parent), db: AsyncSession = Depends(get_db)):
    dob_datetime = datetime.combine(child_data.date_of_birth, datetime.min.time())
    new_child = Child(
        parent_id=current_user.id,
        first_name=child_data.first_name,
        nickname=child_data.nickname,
        date_of_birth=dob_datetime,
        grade_level=child_data.grade_level,
        pin_hash=hash_pin(child_data.pin),
        is_active=True
    )
    db.add(new_child)
    await db.commit()
    await db.refresh(new_child)
    logger.info(f"✅ Child created: {new_child.first_name}")
    return {
        "id": new_child.id,
        "first_name": new_child.first_name,
        "nickname": new_child.nickname,
        "date_of_birth": new_child.date_of_birth.date(),
        "grade_level": new_child.grade_level,
        "is_active": new_child.is_active,
        "created_at": new_child.created_at
    }

@router.get("/", response_model=List[ChildResponse])
async def list_children(current_user: User = Depends(get_current_active_parent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Child).where(Child.parent_id == current_user.id).where(Child.is_active == True))
    children = result.scalars().all()
    return [{"id": c.id, "first_name": c.first_name, "nickname": c.nickname, "date_of_birth": c.date_of_birth.date(), "grade_level": c.grade_level, "is_active": c.is_active, "created_at": c.created_at} for c in children]

@router.post("/verify-pin")
async def verify_child_pin(verify_data: PINVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Child).where(Child.id == verify_data.child_id))
    child = result.scalar_one_or_none()
    if not child or not child.is_active:
        raise HTTPException(status_code=404, detail="Child not found")
    if not verify_pin(verify_data.pin, child.pin_hash):
        raise HTTPException(status_code=401, detail="Incorrect PIN")
    logger.info(f"✅ PIN verified: {child.first_name}")
    return {"verified": True, "child": {"id": child.id, "first_name": child.first_name, "nickname": child.nickname, "grade_level": child.grade_level}}
