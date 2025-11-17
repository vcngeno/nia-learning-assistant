from datetime import datetime, timedelta
from database import students_collection, sessions_collection, activity_logs_collection
from typing import Optional

async def start_session(student_id: str) -> dict:
    """Start a learning session for a student"""
    # Get student
    student = await students_collection.find_one({"student_id": student_id})
    if not student:
        return {"success": False, "error": "Student not found"}
    
    # Check if already in session
    if student.get("session_start"):
        return {"success": False, "error": "Session already active"}
    
    # Reset daily usage if it's a new day
    last_active = student.get("last_active")
    if last_active:
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)
        if last_active.date() < datetime.utcnow().date():
            await students_collection.update_one(
                {"student_id": student_id},
                {"$set": {"daily_usage_minutes": 0}}
            )
    
    # Start session
    session_start = datetime.utcnow()
    await students_collection.update_one(
        {"student_id": student_id},
        {
            "$set": {
                "session_start": session_start.isoformat(),
                "last_active": session_start.isoformat()
            }
        }
    )
    
    # Create session record
    await sessions_collection.insert_one({
        "student_id": student_id,
        "session_start": session_start,
        "session_end": None,
        "total_questions": 0,
        "topics_covered": []
    })
    
    return {"success": True, "session_start": session_start.isoformat()}

async def end_session(student_id: str) -> dict:
    """End a learning session"""
    student = await students_collection.find_one({"student_id": student_id})
    if not student:
        return {"success": False, "error": "Student not found"}
    
    session_start = student.get("session_start")
    if not session_start:
        return {"success": False, "error": "No active session"}
    
    # Calculate session duration
    if isinstance(session_start, str):
        session_start = datetime.fromisoformat(session_start)
    
    session_end = datetime.utcnow()
    duration_minutes = int((session_end - session_start).total_seconds() / 60)
    
    # Update student
    current_usage = student.get("daily_usage_minutes", 0)
    await students_collection.update_one(
        {"student_id": student_id},
        {
            "$set": {
                "session_start": None,
                "daily_usage_minutes": current_usage + duration_minutes,
                "last_active": session_end.isoformat()
            }
        }
    )
    
    # Update session record
    await sessions_collection.update_one(
        {"student_id": student_id, "session_end": None},
        {"$set": {"session_end": session_end}}
    )
    
    return {
        "success": True,
        "session_duration_minutes": duration_minutes,
        "total_usage_today": current_usage + duration_minutes
    }

async def check_time_limit(student_id: str) -> dict:
    """Check if student has exceeded daily time limit"""
    from database import parents_collection
    
    student = await students_collection.find_one({"student_id": student_id})
    if not student:
        return {"allowed": False, "reason": "Student not found"}
    
    # Get student's settings (prioritize student-level settings)
    allowed_hours = student.get("allowed_hours", {"start": 8, "end": 20})
    time_limit = student.get("daily_time_limit", 60)
    
    # Check current usage
    daily_usage = student.get("daily_usage_minutes", 0)
    time_remaining = time_limit - daily_usage
    
    if time_remaining <= 0:
        return {
            "allowed": False,
            "reason": "Daily time limit reached",
            "time_remaining": 0
        }
    
    # Check allowed hours
    current_hour = datetime.utcnow().hour
    allowed_start = allowed_hours.get("start", 8)
    allowed_end = allowed_hours.get("end", 20)
    
    if not (allowed_start <= current_hour < allowed_end):
        return {
            "allowed": False,
            "reason": f"Outside allowed hours ({allowed_start}:00 - {allowed_end}:00)",
            "time_remaining": time_remaining
        }
    
    return {
        "allowed": True,
        "time_remaining": time_remaining
    }

async def log_activity(student_id: str, question: str, response: str, 
                      question_type: Optional[str] = None, flagged: bool = False,
                      flag_reason: Optional[str] = None):
    """Log a student activity"""
    log_doc = {
        "student_id": student_id,
        "timestamp": datetime.utcnow(),
        "question": question,
        "response": response,
        "question_type": question_type,
        "flagged": flagged,
        "flag_reason": flag_reason,
        "session_duration": 0
    }
    
    await activity_logs_collection.insert_one(log_doc)
    
    return {"success": True}
