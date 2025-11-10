from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class ParentCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN")
    
    @validator('pin')
    def pin_must_be_numeric(cls, v):
        if not v.isdigit():
            raise ValueError('PIN must contain only digits')
        return v

class ParentLogin(BaseModel):
    email: EmailStr
    pin: str

class ParentResponse(BaseModel):
    parent_id: str
    email: str
    name: str
    phone: Optional[str]
    children: List[str] = []
    preferences: Dict[str, Any]
    created_at: str

class ParentPreferences(BaseModel):
    daily_time_limit: int = Field(60, ge=15, le=240, description="Daily time limit in minutes")
    content_restrictions: List[str] = Field(default_factory=list)
    email_notifications: bool = True
    weekly_reports: bool = True
    require_approval_for_topics: List[str] = Field(default_factory=list)
    block_keywords: List[str] = Field(default_factory=list)
    allowed_hours_start: int = Field(8, ge=0, le=23)
    allowed_hours_end: int = Field(20, ge=0, le=23)

class AllowedHours(BaseModel):
    start: int = Field(default=8, ge=0, le=23)
    end: int = Field(default=20, ge=1, le=24)

class StudentCreateWithParent(BaseModel):
    parent_id: str
    name: str
    age: int = Field(..., ge=5, le=18)
    grade: int = Field(..., ge=1, le=12)
    reading_level: Optional[int] = None
    special_needs: Optional[List[str]] = Field(default_factory=list)
    interests: Optional[List[str]] = Field(default_factory=list)
    allowed_hours: Optional[AllowedHours] = Field(default_factory=lambda: AllowedHours())
    daily_time_limit: Optional[int] = Field(default=60, ge=0, le=480)
class ActivityLogCreate(BaseModel):
    student_id: str
    question: str
    response: str
    flagged: bool = False
    flag_reason: Optional[str] = None
    question_type: Optional[str] = None

class SessionUpdate(BaseModel):
    student_id: str
    action: str  # "start" or "end"

class ParentDashboardResponse(BaseModel):
    student_name: str
    total_time_today: int  # minutes
    questions_today: int
    topics_explored: List[str]
    recent_conversations: List[Dict[str, Any]]
    flagged_content: List[Dict[str, Any]]
    time_remaining: int  # minutes
    achievements: List[str]
    usage_by_day: Dict[str, int]  # last 7 days

class ActivityReportResponse(BaseModel):
    student_id: str
    student_name: str
    date_range: str
    total_questions: int
    total_time_minutes: int
    topics_breakdown: Dict[str, int]
    flagged_items: List[Dict[str, Any]]
    learning_progress: Dict[str, Any]
