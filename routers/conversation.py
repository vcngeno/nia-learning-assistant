"""Conversation router without LSI (temporary)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging
import openai
import os

from database import get_db
from models import Conversation, Message, Child

router = APIRouter(prefix="/conversation", tags=["Conversation"])
logger = logging.getLogger("routers.conversation")

class MessageCreate(BaseModel):
    child_id: int
    text: str
    conversation_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    text: str
    timestamp: datetime

@router.post("/message", response_model=MessageResponse)
async def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    """Send message and get AI response"""
    try:
        result = await db.execute(select(Child).where(Child.id == message.child_id))
        child = result.scalar_one_or_none()
    except AttributeError:
        child = db.query(Child).filter(Child.id == message.child_id).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if not message.conversation_id:
        conversation = Conversation(
            child_id=child.id,
            title=message.text[:50],
            folder="General",
            message_count=0
        )
        db.add(conversation)
        try:
            await db.commit()
            await db.refresh(conversation)
        except AttributeError:
            db.commit()
            db.refresh(conversation)
    else:
        try:
            result = await db.execute(select(Conversation).where(Conversation.id == message.conversation_id))
            conversation = result.scalar_one_or_none()
        except AttributeError:
            conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message.text
    )
    db.add(user_message)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are Nia, a patient tutor for {child.grade_level} students."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        ai_text = response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        ai_text = "I'm having trouble right now. Can you try asking in a different way?"

    ai_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_text
    )
    db.add(ai_message)

    conversation.message_count += 2
    conversation.updated_at = datetime.utcnow()

    try:
        await db.commit()
        await db.refresh(ai_message)
    except AttributeError:
        db.commit()
        db.refresh(ai_message)

    return MessageResponse(
        id=ai_message.id,
        conversation_id=conversation.id,
        text=ai_text,
        timestamp=ai_message.created_at
    )

@router.get("/conversations/{child_id}")
async def get_conversations(child_id: int, db: Session = Depends(get_db)):
    """Get conversations for a child"""
    try:
        query = select(Conversation).where(Conversation.child_id == child_id)
        result = await db.execute(query.order_by(Conversation.updated_at.desc()))
        conversations = result.scalars().all()
    except AttributeError:
        conversations = db.query(Conversation).filter(
            Conversation.child_id == child_id
        ).order_by(Conversation.updated_at.desc()).all()

    return {"conversations": [
        {
            "id": c.id,
            "title": c.title,
            "folder": c.folder,
            "message_count": c.message_count,
            "updated_at": c.updated_at
        }
        for c in conversations
    ]}
