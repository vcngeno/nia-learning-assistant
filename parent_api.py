from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from models_parent import (
    ParentCreate, ParentLogin, ParentResponse, ParentPreferences,
    StudentCreateWithParent, ParentDashboardResponse, ActivityReportResponse
)
from database import (
    parents_collection, students_collection, activity_logs_collection,
    sessions_collection
)
from auth_utils import (
    hash_pin, verify_pin, create_access_token, verify_token,
    generate_parent_id, generate_student_id
)

router = APIRouter(prefix="/parents", tags=["parents"])

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

async def get_current_parent(authorization: Optional[str] = Header(None)):
    """Dependency to get current authenticated parent"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    parent_id = payload.get("parent_id")
    parent = await parents_collection.find_one({"parent_id": parent_id})
    
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    return parent

@router.post("/register", response_model=dict)
async def register_parent(parent_data: ParentCreate):
    """Register a new parent account"""
    # Check if email already exists
    existing = await parents_collection.find_one({"email": parent_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create parent document
    parent_id = generate_parent_id()
    hashed_pin = hash_pin(parent_data.pin)
    
    parent_doc = {
        "parent_id": parent_id,
        "email": parent_data.email,
        "name": parent_data.name,
        "phone": parent_data.phone,
        "pin": hashed_pin,
        "children": [],
        "preferences": {
            "daily_time_limit": 60,
            "content_restrictions": [],
            "email_notifications": True,
            "weekly_reports": True,
            "require_approval_for_topics": [],
            "block_keywords": [],
            "allowed_hours_start": 8,
            "allowed_hours_end": 20
        },
        "created_at": datetime.utcnow().isoformat()
    }
    
    await parents_collection.insert_one(parent_doc)
    
    # Send welcome email
    await send_welcome_email(parent_data.email, parent_data.name)
    
    # Create access token
    access_token = create_access_token({"parent_id": parent_id, "email": parent_data.email})
    
    return {
        "success": True,
        "parent_id": parent_id,
        "access_token": access_token,
        "message": f"Welcome, {parent_data.name}! Your parent account has been created."
    }

@router.post("/login")
async def login_parent(login_data: ParentLogin):
    """Parent login with email and PIN"""
    parent = await parents_collection.find_one({"email": login_data.email})
    
    if not parent or not verify_pin(login_data.pin, parent["pin"]):
        raise HTTPException(status_code=401, detail="Invalid email or PIN")
    
    access_token = create_access_token({
        "parent_id": parent["parent_id"],
        "email": parent["email"]
    })
    
    return {
        "success": True,
        "access_token": access_token,
        "parent_id": parent["parent_id"],
        "name": parent["name"]
    }

@router.post("/students/create")
async def create_student_for_parent(
    student_data: StudentCreateWithParent,
    parent = Depends(get_current_parent)
):
    """Create a new student linked to parent account"""
    # Verify parent_id matches authenticated parent
    if student_data.parent_id != parent["parent_id"]:
        raise HTTPException(status_code=403, detail="Cannot create student for another parent")
    
    student_id = generate_student_id()
    
    student_doc = {
        "student_id": student_id,
        "parent_id": student_data.parent_id,
        "name": student_data.name,
        "age": student_data.age,
        "grade": student_data.grade,
        "reading_level": student_data.reading_level or student_data.grade,
        "special_needs": student_data.special_needs or [],
        "interests": student_data.interests or [],
        "conversation_history": [],
        "progress": {},
        "daily_usage_minutes": 0,
        "last_active": None,
        "session_start": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await students_collection.insert_one(student_doc)
    
    # Add student to parent's children list
    await parents_collection.update_one(
        {"parent_id": parent["parent_id"]},
        {"$push": {"children": student_id}}
    )
    
    return {
        "success": True,
        "student_id": student_id,
        "message": f"Student {student_data.name} created successfully!"
    }

@router.get("/dashboard/{student_id}", response_model=ParentDashboardResponse)
async def get_parent_dashboard(
    student_id: str,
    parent = Depends(get_current_parent)
):
    """Get parent dashboard for a specific student"""
    # Verify student belongs to parent
    student = await students_collection.find_one({"student_id": student_id})
    
    if not student or student["parent_id"] != parent["parent_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get today's activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_logs = await activity_logs_collection.find({
        "student_id": student_id,
        "timestamp": {"$gte": today_start}
    }).to_list(length=1000)
    
    # Get last 7 days usage
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_logs = await activity_logs_collection.find({
        "student_id": student_id,
        "timestamp": {"$gte": week_ago}
    }).to_list(length=1000)
    
    # Calculate metrics
    total_time_today = student.get("daily_usage_minutes", 0)
    questions_today = len(today_logs)
    
    topics_explored = list(set([
        log.get("question_type", "General")
        for log in today_logs
        if log.get("question_type")
    ]))
    
    recent_conversations = [
        {
            "timestamp": log["timestamp"].isoformat() if isinstance(log["timestamp"], datetime) else log["timestamp"],
            "question": log["question"],
            "response": log["response"][:200] + "..." if len(log["response"]) > 200 else log["response"]
        }
        for log in sorted(today_logs, key=lambda x: x["timestamp"], reverse=True)[:10]
    ]
    
    flagged_content = [
        {
            "timestamp": log["timestamp"].isoformat() if isinstance(log["timestamp"], datetime) else log["timestamp"],
            "question": log["question"],
            "reason": log.get("flag_reason", "Unknown")
        }
        for log in today_logs
        if log.get("flagged", False)
    ]
    
    # Calculate usage by day
    usage_by_day = {}
    for i in range(7):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_logs = [log for log in week_logs if day_start <= log["timestamp"] < day_end]
        usage_by_day[day] = len(day_logs)
    
    time_limit = parent["preferences"]["daily_time_limit"]
    time_remaining = max(0, time_limit - total_time_today)
    
    return ParentDashboardResponse(
        student_name=student["name"],
        total_time_today=total_time_today,
        questions_today=questions_today,
        topics_explored=topics_explored,
        recent_conversations=recent_conversations,
        flagged_content=flagged_content,
        time_remaining=time_remaining,
        achievements=student.get("achievements", []),
        usage_by_day=usage_by_day
    )

@router.get("/students")
async def get_parent_students(parent = Depends(get_current_parent)):
    """Get all students for this parent"""
    students = await students_collection.find({
        "parent_id": parent["parent_id"]
    }).to_list(length=100)
    
    return {
        "success": True,
        "students": [
            {
                "student_id": s["student_id"],
                "name": s["name"],
                "age": s["age"],
                "grade": s["grade"]
            }
            for s in students
        ]
    }

@router.put("/preferences")
async def update_preferences(
    preferences: ParentPreferences,
    parent = Depends(get_current_parent)
):
    """Update parent preferences"""
    await parents_collection.update_one(
        {"parent_id": parent["parent_id"]},
        {"$set": {"preferences": preferences.dict()}}
    )
    
    return {"success": True, "message": "Preferences updated"}

@router.get("/activity-report/{student_id}")
async def get_activity_report(
    student_id: str,
    days: int = 7,
    parent = Depends(get_current_parent)
):
    """Get detailed activity report for a student"""
    student = await students_collection.find_one({"student_id": student_id})
    
    if not student or student["parent_id"] != parent["parent_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = await activity_logs_collection.find({
        "student_id": student_id,
        "timestamp": {"$gte": start_date}
    }).to_list(length=10000)
    
    # Analyze topics
    topics_breakdown = {}
    for log in logs:
        topic = log.get("question_type", "General")
        topics_breakdown[topic] = topics_breakdown.get(topic, 0) + 1
    
    # Get flagged items
    flagged_items = [
        {
            "timestamp": log["timestamp"].isoformat(),
            "question": log["question"],
            "reason": log.get("flag_reason", "")
        }
        for log in logs
        if log.get("flagged", False)
    ]
    
    total_time = sum([log.get("session_duration", 0) for log in logs]) // 60
    
    return ActivityReportResponse(
        student_id=student_id,
        student_name=student["name"],
        date_range=f"Last {days} days",
        total_questions=len(logs),
        total_time_minutes=total_time,
        topics_breakdown=topics_breakdown,
        flagged_items=flagged_items,
        learning_progress={"questions_per_day": len(logs) / days}
    )

async def send_welcome_email(email: str, name: str):
    """Send welcome email to new parent"""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Email not configured, skipping welcome email")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = email
        msg['Subject'] = "Welcome to Nia Learning Assistant!"
        
        body = f"""
        Dear {name},
        
        Welcome to Nia! Your parent account has been successfully created.
        
        You can now:
        - Create student profiles for your children
        - Monitor their learning activity
        - Set time limits and content restrictions
        - Receive weekly progress reports
        
        Best regards,
        The Nia Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
