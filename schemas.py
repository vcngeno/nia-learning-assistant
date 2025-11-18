from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Parent/User Schemas
class ParentCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

class ParentResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Child Schemas
class ChildCreate(BaseModel):
    first_name: str
    nickname: Optional[str] = None
    date_of_birth: datetime
    grade_level: str
    pin: str = Field(..., min_length=4, max_length=6)

class ChildLogin(BaseModel):
    username: str  # This will be first_name in the backend
    pin: str

class ChildResponse(BaseModel):
    id: int
    first_name: str
    nickname: Optional[str]
    grade_level: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    user_type: Optional[str] = None

# Conversation Schemas
class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    source_type: Optional[str]
    depth_level: int
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    title: str
    folder: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
