from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid, logging
from datetime import datetime
from database import get_db
from models import Conversation as DBConversation, Message as DBMessage, Child
from services.conversation_service import ConversationService
from services.rag_service import get_rag_service
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)

class MessageCreate(BaseModel):
    conversation_id: Optional[str] = None
    child_id: str
    text: str
    grade_level: str = "2nd grade"
    current_depth: int = 1

class MessageResponse(BaseModel):
    message_id: str
    conversation_id: int
    text: str
    tutoring_depth_level: int
    follow_up_offered: bool
    source_citations: List[Dict]
    source_type: str
    source_label: str
    generated_visuals: List[Dict]
    related_topics: List[str]
    model_used: str

def calculate_age(dob: datetime) -> int:
    today = datetime.now()
    age = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1
    return age

@router.post("/message", response_model=MessageResponse)
async def send_message(message: MessageCreate, db: AsyncSession = Depends(get_db)):
    try:
        child_id = int(message.child_id)
        child = (await db.execute(select(Child).where(Child.id == child_id))).scalar_one_or_none()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        
        child_age = calculate_age(child.date_of_birth) if child.date_of_birth else None
        
        conversation = None
        if message.conversation_id:
            conversation = (await db.execute(select(DBConversation).where(DBConversation.id == int(message.conversation_id)))).scalar_one_or_none()
        
        if not conversation:
            conversation = DBConversation(child_id=child_id, title=message.text[:50], folder="General", topics=[], message_count=0, total_depth_reached=1)
            db.add(conversation)
            await db.flush()
        
        user_msg = DBMessage(conversation_id=conversation.id, role="child", content=message.text, depth_level=message.current_depth)
        db.add(user_msg)
        
        rag = get_rag_service()
        result = rag.query(question=message.text, grade_level=message.grade_level, depth_level=message.current_depth, child_age=child_age)
        
        sources = [{"title": "Web Search", "type": "web_search", "query": s.get("query", ""), "verified": True} for s in result.get("sources", []) if s.get("type") == "web_search"]
        
        conv_service = ConversationService()
        response = conv_service.format_response_with_sources(answer=result["answer"], sources=sources, depth_level=message.current_depth)
        
        response["source_type"] = "web_search" if result.get("used_web_search") else "general_knowledge"
        response["source_label"] = "🌐 From the web" if result.get("used_web_search") else "ℹ️ From what I know"
        
        ai_msg = DBMessage(conversation_id=conversation.id, role="assistant", content=result["answer"], model_used=result["model_used"], source_type=response["source_type"], sources=sources, depth_level=message.current_depth)
        db.add(ai_msg)
        
        conversation.message_count += 2
        child.last_active = user_msg.created_at
        
        await db.commit()
        await db.refresh(conversation)
        
        response["message_id"] = str(uuid.uuid4())
        response["conversation_id"] = conversation.id
        response["model_used"] = result["model_used"]
        
        logger.info(f"✅ Message processed for child {child_id}")
        return response
    except Exception as e:
        await db.rollback()
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
