from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from datetime import datetime
import os
from dotenv import load_dotenv

from safety_filter import ChildSafetyFilter
from enhanced_tutor import NiaTutor
# ✨ NEW: Import the question handler
from question_handler import classify_question, get_response_strategy

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
    title="Nia API",
    description="An Intelligent Learning Summarization Assistant for Children",
    version="2.0.0"
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://web-production-a4ec.up.railway.app",
        "https://*.railway.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

safety_filter = ChildSafetyFilter()
tutor = NiaTutor(safety_filter)
students_db = {}

class StudentCreate(BaseModel):
    name: str
    age: int
    grade: int
    reading_level: Optional[int] = None
    special_needs: Optional[List[str]] = []
    interests: Optional[List[str]] = []

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

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Nia - Your Intelligent Learning Assistant",
        "version": "2.0.0",
        "project_lead": "Vanessa Ngeno",
        "status": "operational",
        "features": ["intelligent_question_classification", "adaptive_responses"]
    }

@app.post("/students/create")
def create_student(data: StudentCreate):
    student_id = f"student_{len(students_db) + 1}_{int(datetime.now().timestamp())}"
    
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
    
    students_db[student_id] = student
    
    return {
        "success": True,
        "student_id": student_id,
        "message": f"Welcome, {data.name}! I'm Nia, ready to help you learn! 📚✨"
    }

@app.post("/chat")
def chat(chat_data: ChatMessage):
    """
    ENHANCED: Now with intelligent question classification
    """
    if chat_data.student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = students_db[chat_data.student_id]
    
    # NEW: Classify the question type
    question_type = classify_question(chat_data.message)
    strategy = get_response_strategy(question_type)
    
    # NEW: Pass the strategy to the tutor for enhanced responses
    result = tutor.chat(
        student, 
        chat_data.message,
        question_type=question_type.value,
        response_strategy=strategy
    )
    
    return {
        "success": result['success'],
        "response": result['response'],
        "question_type": question_type.value,
        "needs_intervention": result.get('needs_intervention', False),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/summarize")
def summarize_content(data: SummarizeRequest):
    if data.student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = students_db[data.student_id]
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
def process_study_material(data: StudyMaterialRequest):
    if data.student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")
    
    student = students_db[data.student_id]
    result = tutor.process_study_material(data.material, student)
    
    return {
        "success": True,
        "summary": result['summary'],
        "key_points": result['key_points'],
        "practice_questions": result['practice_questions'] if data.generate_questions else None,
        "reading_time_minutes": result['reading_time_minutes'],
        "compression_ratio": result['compression_ratio']
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_students": len(students_db),
        "service": "Nia Learning Assistant",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
