from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime
import os
from dotenv import load_dotenv
import requests
import json

from safety_filter import ChildSafetyFilter
from enhanced_tutor import NiaTutor
from question_handler import classify_question, get_response_strategy

# NEW: Import parental control modules
from database import init_db, close_db, students_collection, parents_collection
from parent_api import router as parent_router
from time_tracking import (
    start_session, end_session, check_time_limit, log_activity
)
from auth_utils import generate_student_id

import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

load_dotenv()

app = FastAPI(
    title="Nia API with Parental Controls",
    description="An Intelligent Learning Assistant for Children with Comprehensive Parental Monitoring",
    version="3.0.0"
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://web-production-a4ec.up.railway.app",
        "https://*.railway.app",
        "https://*.streamlit.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include parent router
app.include_router(parent_router)

safety_filter = ChildSafetyFilter()

# Legacy in-memory storage for backwards compatibility
students_db = {}


# ============= Weather and Date Functions =============
def get_current_datetime():
    """Get current date and time"""
    now = datetime.now()
    return {
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M %p"),
        "timezone": "EST",
        "iso": now.isoformat()
    }

def get_weather(location: str):
    """Get current weather for a location"""
    api_key = os.getenv("WEATHER_API_KEY")
    
    if not api_key:
        return {"error": "Weather API key not configured"}
    
    try:
        response = requests.get(
            "https://api.weatherapi.com/v1/current.json",
            params={"key": api_key, "q": location, "aqi": "no"},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "location": data["location"]["name"],
            "country": data["location"]["country"],
            "temperature_f": data["current"]["temp_f"],
            "temperature_c": data["current"]["temp_c"],
            "condition": data["current"]["condition"]["text"],
            "humidity": data["current"]["humidity"],
            "feels_like_f": data["current"]["feelslike_f"]
        }
    except Exception as e:
        return {"error": f"Could not fetch weather: {str(e)}"}

# Map function names to actual functions
AVAILABLE_FUNCTIONS = {
    "get_current_datetime": get_current_datetime,
    "get_weather": get_weather
}

# Tools definition for OpenAI
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time. Use when student asks about date or time.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location. Use when student asks about weather.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name (e.g., 'New York')"}
                },
                "required": ["location"]
            }
        }
    }
]
# ============= End Weather and Date Functions =============

# Connect tools to tutor

# Initialize tutor
tutor = NiaTutor(safety_filter)

# Connect tools to tutor
tutor.set_tools(OPENAI_TOOLS, AVAILABLE_FUNCTIONS)


class StudentCreate(BaseModel):
    name: str
    age: int
    grade: int
    reading_level: Optional[int] = None
    special_needs: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    parent_id: Optional[str] = None  # NEW: Optional parent link

class ChatMessage(BaseModel):
    student_id: str
    message: str

class SummarizeRequest(BaseModel):
    student_id: str
    content: str

class StudyMaterialRequest(BaseModel):
    student_id: str
    material: str
    generate_questions: Optional[bool] = True

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    print("🚀 Nia API with Parental Controls started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""
    await close_db()
    print("👋 Nia API shutting down...")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Nia - Your Intelligent Learning Assistant with Parental Controls",
        "version": "3.0.0",
        "project_lead": "Vanessa Ngeno",
        "status": "operational",
        "features": [
            "intelligent_question_classification",
            "adaptive_responses",
            "parental_dashboard",
            "time_limits",
            "content_monitoring",
            "activity_reports"
        ]
    }

@app.post("/students/create")
async def create_student(data: StudentCreate):
    """Create a new student (with optional parent link)"""
    student_id = generate_student_id()
    
    # Create student profile for tutor
    student = tutor.create_student_profile(
        name=data.name,
        age=data.age,
        grade=data.grade,
        reading_level=data.reading_level,
        special_needs=data.special_needs
    )
    
    student['id'] = student_id
    student['interests'] = data.interests
    student['created_at'] = datetime.now().isoformat()
    student['parent_id'] = data.parent_id
    
    # Store in MongoDB
    student_doc = {
        "student_id": student_id,
        "parent_id": data.parent_id,
        "name": data.name,
        "age": data.age,
        "grade": data.grade,
        "reading_level": data.reading_level or data.grade,
        "special_needs": data.special_needs or [],
        "interests": data.interests or [],
        "conversation_history": [],
        "progress": {},
        "daily_usage_minutes": 0,
        "last_active": None,
        "session_start": None,
        "created_at": datetime.utcnow().isoformat()
    }
    
    await students_collection.insert_one(student_doc)
    
    # Also keep in memory for backwards compatibility
    students_db[student_id] = student
    
    # If has parent, add to parent's children
    if data.parent_id:
        await parents_collection.update_one(
            {"parent_id": data.parent_id},
            {"$addToSet": {"children": student_id}}
        )
    
    return {
        "success": True,
        "student_id": student_id,
        "message": f"Welcome, {data.name}! I'm Nia, ready to help you learn! 📚✨"
    }

@app.post("/chat")
async def chat(chat_data: ChatMessage):
    """Chat endpoint with parental controls"""
    # Check if student exists in MongoDB first
    student_doc = await students_collection.find_one({"student_id": chat_data.student_id})
    
    if not student_doc:
        # Fallback to in-memory for backwards compatibility
        if chat_data.student_id not in students_db:
            raise HTTPException(status_code=404, detail="Student not found")
        student = students_db[chat_data.student_id]
    else:
        # Use MongoDB student
        student = student_doc
        
        # NEW: Check time limits and parental controls
        time_check = await check_time_limit(chat_data.student_id)
        
        if not time_check["allowed"]:
            return {
                "success": False,
                "response": f"⏰ Learning time is over for today. {time_check['reason']}. Ask your parent for more time!",
                "time_limited": True,
                "reason": time_check["reason"]
            }
        
        # Start session if not already started
        if not student.get("session_start"):
            await start_session(chat_data.student_id)
        
        # Check content restrictions
        parent_id = student.get("parent_id")
        if parent_id:
            parent = await parents_collection.find_one({"parent_id": parent_id})
            if parent:
                blocked_keywords = parent.get("preferences", {}).get("block_keywords", [])
                for keyword in blocked_keywords:
                    if keyword.lower() in chat_data.message.lower():
                        await log_activity(
                            chat_data.student_id,
                            chat_data.message,
                            "Content blocked by parent",
                            flagged=True,
                            flag_reason=f"Blocked keyword: {keyword}"
                        )
                        return {
                            "success": False,
                            "response": "I can't answer that question. Please ask about something else!",
                            "blocked": True
                        }
    
    # Classify question
    question_type = classify_question(chat_data.message)
    strategy = get_response_strategy(question_type)
    
    # Get response from tutor
    result = tutor.chat(
        student, 
        chat_data.message,
        question_type=question_type.value,
        response_strategy=strategy
    )
    
    # Log activity to MongoDB
    if student_doc:
        await log_activity(
            chat_data.student_id,
            chat_data.message,
            result['response'],
            question_type=question_type.value,
            flagged=result.get('needs_intervention', False),
            flag_reason="Crisis intervention needed" if result.get('needs_intervention') else None
        )
        
        # Update last active
        await students_collection.update_one(
            {"student_id": chat_data.student_id},
            {"$set": {"last_active": datetime.utcnow().isoformat()}}
        )
    
    return {
        "success": result['success'],
        "response": result['response'],
        "question_type": question_type.value,
        "needs_intervention": result.get('needs_intervention', False),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/session/end/{student_id}")
async def end_student_session(student_id: str):
    """End a student's learning session"""
    result = await end_session(student_id)
    return result

@app.get("/session/check/{student_id}")
async def check_session_status(student_id: str):
    """Check if student can start/continue session"""
    time_check = await check_time_limit(student_id)
    return time_check

@app.post("/summarize")
async def summarize_content(data: SummarizeRequest):
    """Summarize content for student"""
    student_doc = await students_collection.find_one({"student_id": data.student_id})
    
    if not student_doc:
        if data.student_id not in students_db:
            raise HTTPException(status_code=404, detail="Student not found")
        student = students_db[data.student_id]
    else:
        student = student_doc
    
    summary_result = tutor.summarize_content(data.content, student)
    
    return {
        "success": True,
        "summary": summary_result['summary'],
        "original_length": summary_result['original_length'],
        "summary_length": summary_result['summary_length'],
        "compression_ratio": f"{summary_result['compression_ratio']:.1%}",
        "grade_level": summary_result['grade_level'],
        "reading_time_minutes": summary_result['summary_length'] // 50
    }

@app.post("/study/process")
async def process_study_material(data: StudyMaterialRequest):
    """Process study material for student"""
    student_doc = await students_collection.find_one({"student_id": data.student_id})
    
    if not student_doc:
        if data.student_id not in students_db:
            raise HTTPException(status_code=404, detail="Student not found")
        student = students_db[data.student_id]
    else:
        student = student_doc
    
    result = tutor.process_study_material(data.material, student)
    
    return {
        "success": True,
        "summary": result['summary'],
        "key_points": result['key_points'],
        "practice_questions": result['practice_questions'] if data.generate_questions else None,
        "reading_time_minutes": result['reading_time_minutes'],
        "compression_ratio": result['compression_ratio']
    }


@app.get("/debug/tools")
def debug_tools():
    """Debug endpoint to check if tools are configured"""
    return {
        "tools_configured": tutor.tools is not None,
        "num_tools": len(tutor.tools) if tutor.tools else 0,
        "available_functions": list(tutor.available_functions.keys()) if tutor.available_functions else [],
        "model": "gpt-4o"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_students": len(students_db),
        "service": "Nia Learning Assistant with Parental Controls",
        "version": "3.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
