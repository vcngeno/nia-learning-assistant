"""
Enhanced conversation router with LSI retrieval and folder organization
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import logging

from database import get_db
from models import Conversation, Message, Child
from model.lsi_retriever import LSIRetriever
from model.rewriter import AgeAppropriateRewriter
import openai
import os

router = APIRouter(prefix="/conversation", tags=["Conversation"])
logger = logging.getLogger("routers.conversation")

# Initialize LSI retriever and rewriter
retriever = LSIRetriever()
rewriter = AgeAppropriateRewriter()

class MessageCreate(BaseModel):
    child_id: int
    text: str
    conversation_id: Optional[int] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    text: str
    folder: str
    sources: List[dict]
    timestamp: datetime

@router.post("/message", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send message and get AI response with LSI retrieval"""

    # Get child info
    try:
        result = await db.execute(select(Child).where(Child.id == message.child_id))
        child = result.scalar_one_or_none()
    except AttributeError:
        child = db.query(Child).filter(Child.id == message.child_id).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Get or create conversation
    if message.conversation_id:
        try:
            result = await db.execute(select(Conversation).where(Conversation.id == message.conversation_id))
            conversation = result.scalar_one_or_none()
        except AttributeError:
            conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
    else:
        conversation = None

    if not conversation:
        # Create new conversation
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

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message.text
    )
    db.add(user_message)

    # Retrieve relevant content using LSI
    relevant_docs = retriever.retrieve(
        query=message.text,
        top_k=3,
        grade_level=child.grade_level
    )

    # Build context for AI
    context = "\n\n".join([
        f"Source: {doc.get('topic', 'Unknown')}\n{doc['content']}"
        for doc in relevant_docs
    ])

    # Get AI response
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f"""You are Nia, a kind learning assistant for {child.grade_level} students.

Context from curriculum:
{context}

Student question: {message.text}

Provide a helpful, age-appropriate answer. Keep it simple and encouraging."""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Nia, a patient and encouraging tutor for children."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        ai_text = response.choices[0].message.content

        # Rewrite for age-appropriateness
        autism_mode = 'autism_support' in (child.learning_accommodations or [])
        ai_text = rewriter.rewrite(ai_text, child.grade_level, autism_mode)

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        ai_text = "I'm having trouble right now. Can you try asking in a different way?"

    # Determine folder based on content
    folder = _categorize_message(message.text, relevant_docs)
    conversation.folder = folder

    # Save AI response
    ai_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_text,
        sources=[{"title": doc.get('topic'), "relevance": doc.get('relevance_score')} for doc in relevant_docs]
    )
    db.add(ai_message)

    # Update conversation
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
        folder=folder,
        sources=[{"title": doc.get('topic'), "subject": doc.get('subject')} for doc in relevant_docs],
        timestamp=ai_message.created_at
    )

def _categorize_message(text: str, docs: List[dict]) -> str:
    """Categorize message into folder based on content"""
    if not docs:
        return "General"

    # Use subject from most relevant document
    subjects = [doc.get('subject', 'General') for doc in docs]
    return subjects[0] if subjects else "General"

@router.get("/folders/{child_id}")
async def get_folders(child_id: int, db: Session = Depends(get_db)):
    """Get all folders for a child"""
    try:
        result = await db.execute(
            select(Conversation.folder).where(Conversation.child_id == child_id).distinct()
        )
        folders = [row[0] for row in result]
    except AttributeError:
        folders = db.query(Conversation.folder).filter(Conversation.child_id == child_id).distinct().all()
        folders = [f[0] for f in folders]

    return {"folders": folders}

@router.get("/conversations/{child_id}")
async def get_conversations(child_id: int, folder: Optional[str] = None, db: Session = Depends(get_db)):
    """Get conversations for a child, optionally filtered by folder"""
    try:
        query = select(Conversation).where(Conversation.child_id == child_id)
        if folder:
            query = query.where(Conversation.folder == folder)
        result = await db.execute(query.order_by(Conversation.updated_at.desc()))
        conversations = result.scalars().all()
    except AttributeError:
        query = db.query(Conversation).filter(Conversation.child_id == child_id)
        if folder:
            query = query.filter(Conversation.folder == folder)
        conversations = query.order_by(Conversation.updated_at.desc()).all()

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
