"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

# Parent schemas
class ParentCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    parent_id: int
    email: str
    full_name: str

# Child schemas
class ChildCreate(BaseModel):
    first_name: str
    nickname: Optional[str] = None
    date_of_birth: str  # Accept as string, not datetime
    grade_level: str
    pin: str
    preferred_language: Optional[str] = "en"

    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v):
        if len(v) != 4 or not v.isdigit():
            raise ValueError('PIN must be exactly 4 digits')
        return v

class ChildLogin(BaseModel):
    child_id: int
    pin: str

class ChildResponse(BaseModel):
    id: int
    parent_id: int
    first_name: str
    nickname: Optional[str]
    grade_level: str
    created_at: datetime

    class Config:
        from_attributes = True
