from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime

from database import get_db
from models import (
    Conversation as DBConversation,
    Message as DBMessage,
    Child,
    MessageFeedback
)
from services.rag_service import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Enhanced Pydantic Models ====================

class SourceReference(BaseModel):
    """Detailed source reference with links"""
    title: str
    type: str  # "curated_content", "general_knowledge"
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    relevance: Optional[str] = None


class ConversationCreate(BaseModel):
    """Create a new conversation"""
    child_id: int
    title: Optional[str] = "New Conversation"
    folder: Optional[str] = None  # Auto-detected if not provided


class MessageCreate(BaseModel):
    """Send a message in a conversation"""
    child_id: int
    conversation_id: Optional[int] = None
    text: str = Field(..., min_length=1, max_length=5000)
    current_depth: int = Field(default=1, ge=1, le=3)


class MessageFeedbackCreate(BaseModel):
    """Submit feedback on a message"""
    message_id: int
    child_id: int
    is_helpful: bool
    feedback_type: Optional[str] = None
    feedback_text: Optional[str] = None


class MessageResponse(BaseModel):
    """AI response to a message"""
    id: int
    conversation_id: int
    text: str
    language: str
    source_label: str
    has_curated_content: bool
    sources: List[SourceReference]
    follow_up_questions: List[str]
    tutoring_depth_level: int
    max_depth_reached: bool
    model_used: str
    timestamp: datetime


# ==================== Helper Functions ====================

def detect_folder_from_question(question: str, sources: List[Dict] = None) -> str:
    """Detect conversation folder/category from question content"""

    question_lower = question.lower()

    # If we have sources from RAG, use the subject from the most relevant source
    if sources and len(sources) > 0:
        # Use subject from first (most relevant) source
        subject = sources[0].get('subject', 'general')
        folder_mapping = {
            'math': 'Math',
            'science': 'Science',
            'history': 'History',
            'english': 'English',
            'geography': 'Geography'
        }
        return folder_mapping.get(subject, 'General')

    # Fallback to keyword detection
    subject_keywords = {
        'Math': ['math', 'arithmetic', 'algebra', 'geometry', 'fraction', 'multiply', 'divide',
                 'add', 'subtract', 'equation', 'calculate', 'number', 'times', 'plus', 'minus'],
        'Science': ['science', 'biology', 'chemistry', 'physics', 'photosynthesis', 'plant',
                    'animal', 'water cycle', 'energy', 'cell', 'experiment', 'atom', 'molecule'],
        'History': ['history', 'washington', 'revolution', 'american', 'civil war', 'president',
                    'colony', 'ancient', 'historical', 'war', 'battle', 'independence'],
        'English': ['english', 'grammar', 'writing', 'sentence', 'paragraph', 'noun', 'verb',
                    'adjective', 'essay', 'story', 'book', 'read', 'literature'],
        'Geography': ['geography', 'continent', 'ocean', 'state', 'country', 'map', 'capital',
                      'city', 'mountain', 'river', 'climate', 'population'],
        'Travel': ['travel', 'trip', 'vacation', 'visit', 'journey', 'destination', 'tourist',
                   'flight', 'hotel', 'explore', 'adventure']
    }

    # Count keyword matches for each subject
    matches = {}
    for subject, keywords in subject_keywords.items():
        count = sum(1 for keyword in keywords if keyword in question_lower)
        if count > 0:
            matches[subject] = count

    # Return subject with most matches, or 'General' if no matches
    if matches:
        return max(matches.items(), key=lambda x: x[1])[0]

    return 'General'


def generate_conversation_title(question: str, max_length: int = 50) -> str:
    """Generate a concise title from the first question"""

    # Clean up the question
    title = question.strip()

    # Remove question mark and extra spaces
    title = title.replace('?', '').strip()

    # Truncate if too long
    if len(title) > max_length:
        title = title[:max_length-3] + "..."

    # Capitalize first letter
    if title:
        title = title[0].upper() + title[1:]

    return title or "New Conversation"


# ==================== API Endpoints ====================

@router.post("/message", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get AI response with enhanced features:
    - RAG with curated educational content
    - Automatic folder categorization
    - Bilingual support (English/Spanish)
    - Accessibility accommodations
    - 3-level depth tutoring system
    """

    try:
        # Get child profile
        result = await db.execute(
            select(Child).where(Child.id == message_data.child_id)
        )
        child = result.scalar_one_or_none()

        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found"
            )

        # Build child profile for RAG
        child_profile = {
            'grade_level': child.grade_level,
            'preferred_language': child.preferred_language or 'en',
            'reading_level': child.reading_level or 'at grade level',
            'learning_accommodations': child.learning_accommodations or []
        }

        # Get or create conversation
        if message_data.conversation_id:
            # Existing conversation
            conv_result = await db.execute(
                select(DBConversation).where(
                    DBConversation.id == message_data.conversation_id
                )
            )
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            # New conversation - will auto-categorize after getting AI response
            conversation = None

        # Get conversation history if exists
        conversation_history = []
        if conversation:
            history_result = await db.execute(
                select(DBMessage)
                .where(DBMessage.conversation_id == conversation.id)
                .order_by(DBMessage.created_at.desc())
                .limit(10)
            )
            messages = history_result.scalars().all()

            # Format for RAG service (reverse to chronological order)
            for msg in reversed(messages):
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Generate AI response using enhanced RAG
        ai_response = await rag_service.generate_response(
            db=db,
            question=message_data.text,
            child_profile=child_profile,
            conversation_history=conversation_history,
            current_depth=message_data.current_depth
        )

        # Auto-detect folder if creating new conversation
        if not conversation:
            folder = detect_folder_from_question(
                message_data.text,
                ai_response.get('sources', [])
            )

            title = generate_conversation_title(message_data.text)

            # Create new conversation
            conversation = DBConversation(
                child_id=message_data.child_id,
                title=title,
                folder=folder
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            logger.info(f"Created new conversation: {title} in folder: {folder}")

        # Save user message
        user_message = DBMessage(
            conversation_id=conversation.id,
            role="user",
            content=message_data.text
        )
        db.add(user_message)

        # Save AI response
        assistant_message = DBMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=ai_response['text'],
            tutoring_depth_level=message_data.current_depth,
            has_curated_content=ai_response.get('has_curated_content', False),
            model_used=ai_response.get('model_used', 'unknown')
        )
        db.add(assistant_message)

        await db.commit()
        await db.refresh(assistant_message)

        # Format sources for response
        formatted_sources = []
        for source in ai_response.get('sources', []):
            formatted_sources.append(SourceReference(
                title=source.get('title', 'Unknown'),
                type='curated_content' if source.get('subject') else 'general_knowledge',
                subject=source.get('subject'),
                grade_level=source.get('grade_level'),
                relevance=source.get('relevance', 'medium')
            ))

        # Generate follow-up questions based on depth
        follow_up_questions = []
        max_depth_reached = message_data.current_depth >= 3

        if not max_depth_reached:
            if message_data.current_depth == 1:
                follow_up_questions = ["Would you like to learn more about this?"]
            elif message_data.current_depth == 2:
                follow_up_questions = ["Would you like to explore this topic further?"]

        # Return response
        return MessageResponse(
            id=assistant_message.id,
            conversation_id=conversation.id,
            text=ai_response['text'],
            language=child_profile['preferred_language'],
            source_label=ai_response.get('source_label', 'ℹ️ From what I know'),
            has_curated_content=ai_response.get('has_curated_content', False),
            sources=formatted_sources,
            follow_up_questions=follow_up_questions,
            tutoring_depth_level=message_data.current_depth,
            max_depth_reached=max_depth_reached,
            model_used=ai_response.get('model_used', 'unknown'),
            timestamp=assistant_message.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.get("/conversations/{child_id}")
async def get_conversations(
    child_id: int,
    folder: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all conversations for a child, optionally filtered by folder"""

    query = select(DBConversation).where(DBConversation.child_id == child_id)

    if folder:
        query = query.where(DBConversation.folder == folder)

    query = query.order_by(DBConversation.updated_at.desc())

    result = await db.execute(query)
    conversations = result.scalars().all()

    return {
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "folder": conv.folder,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            }
            for conv in conversations
        ]
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a conversation"""

    result = await db.execute(
        select(DBMessage)
        .where(DBMessage.conversation_id == conversation_id)
        .order_by(DBMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
                "tutoring_depth_level": msg.tutoring_depth_level,
                "has_curated_content": msg.has_curated_content
            }
            for msg in messages
        ]
    }


@router.post("/feedback")
async def submit_feedback(
    feedback: MessageFeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback on an AI response"""

    # Create feedback record
    db_feedback = MessageFeedback(
        message_id=feedback.message_id,
        child_id=feedback.child_id,
        is_helpful=feedback.is_helpful,
        feedback_type=feedback.feedback_type,
        feedback_text=feedback.feedback_text
    )

    db.add(db_feedback)
    await db.commit()

    if feedback.is_helpful:
        return {"message": "Thank you for your feedback! This helps Nia learn and improve."}
    else:
        return {"message": "Thank you for letting us know. We'll work on improving this."}


@router.get("/folders/{child_id}")
async def get_folders(
    child_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all unique folders for a child's conversations"""

    result = await db.execute(
        select(DBConversation.folder)
        .where(DBConversation.child_id == child_id)
        .distinct()
    )

    folders = [row[0] for row in result.all() if row[0]]

    return {"folders": sorted(folders)}
