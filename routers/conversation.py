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
from services.conversation_service import ConversationService
from services.rag_service import get_rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Enhanced Pydantic Models ====================

class SourceReference(BaseModel):
    """Detailed source reference with links"""
    title: str
    type: str  # "web_search", "curated_content", "textbook"
    query: Optional[str] = None
    url: Optional[str] = None
    citation_number: Optional[int] = None
    verified: bool = True


class MessageCreate(BaseModel):
    conversation_id: Optional[int] = None
    child_id: int
    text: str
    current_depth: int = Field(default=1, ge=1, le=3)
    continue_exploration: Optional[bool] = False
    # Language is determined from child's profile


class MessageResponse(BaseModel):
    message_id: str
    conversation_id: int
    text: str
    tutoring_depth_level: int
    follow_up_offered: bool
    follow_up_questions: List[str]
    source_references: List[SourceReference]  # Enhanced with links
    source_type: str
    source_label: str
    model_used: str
    max_depth_reached: bool
    language: str  # 'en' or 'es'
    # Accessibility info
    has_text_to_speech: bool
    complexity_level: str  # "simplified", "standard", "advanced"


class MessageFeedbackCreate(BaseModel):
    message_id: int
    child_id: int
    is_helpful: bool
    feedback_type: Optional[str] = None  # "too_complex", "too_simple", "inappropriate", "wrong_info"
    feedback_text: Optional[str] = None


class MessageFeedbackResponse(BaseModel):
    success: bool
    message: str


# ==================== Helper Functions ====================

def get_language_strings(language: str) -> Dict[str, str]:
    """Get UI strings in the appropriate language"""
    strings = {
        "en": {
            "learn_more": "Would you like to learn more about this?",
            "any_questions": "Do you have any questions about what I just explained?",
            "more_detail": "Should I explain any part in more detail?",
            "explore_further": "Would you like to explore this topic further?",
            "see_examples": "Are there specific examples you'd like to see?",
            "connections": "Should we look at how this connects to other topics?",
            "practice": "Would you like to try a practice problem?",
            "real_life": "Should we explore how this is used in real life?",
            "new_topic": "Are you ready to move to a new topic?",
        },
        "es": {
            "learn_more": "¿Te gustaría aprender más sobre esto?",
            "any_questions": "¿Tienes alguna pregunta sobre lo que acabo de explicar?",
            "more_detail": "¿Debería explicar alguna parte con más detalle?",
            "explore_further": "¿Te gustaría explorar este tema más a fondo?",
            "see_examples": "¿Hay ejemplos específicos que te gustaría ver?",
            "connections": "¿Deberíamos ver cómo esto se conecta con otros temas?",
            "practice": "¿Te gustaría intentar un problema de práctica?",
            "real_life": "¿Deberíamos explorar cómo se usa esto en la vida real?",
            "new_topic": "¿Estás listo para pasar a un nuevo tema?",
        }
    }
    return strings.get(language, strings["en"])


def generate_follow_up_questions(
    depth_level: int,
    language: str = "en"
) -> List[str]:
    """Generate contextual follow-up questions in the appropriate language"""
    strings = get_language_strings(language)

    if depth_level == 1:
        return [
            strings["learn_more"],
            strings["any_questions"],
            strings["more_detail"]
        ]
    elif depth_level == 2:
        return [
            strings["explore_further"],
            strings["see_examples"],
            strings["connections"]
        ]
    else:
        return [
            strings["practice"],
            strings["real_life"],
            strings["new_topic"]
        ]


def format_answer_with_depth(
    answer: str,
    depth_level: int,
    language: str = "en"
) -> str:
    """Format answer based on depth level and language"""

    if language == "es":
        prefixes = {
            1: "📚 Déjame explicarte:\n\n",
            2: "🔍 Exploremos más a fondo:\n\n",
            3: "🎯 Aquí está la explicación avanzada:\n\n"
        }
    else:
        prefixes = {
            1: "📚 Let me explain:\n\n",
            2: "🔍 Let's explore deeper:\n\n",
            3: "🎯 Here's the advanced explanation:\n\n"
        }

    prefix = prefixes.get(depth_level, prefixes[1])

    # Don't add prefix if answer already has emoji indicators
    if not any(emoji in answer for emoji in ["📚", "🔍", "🎯", "🌐", "ℹ️"]):
        return prefix + answer

    return answer


# ==================== Main Chat Endpoint with Full Features ====================

@router.post("/message", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Enhanced chat endpoint with:
    - Bilingual support (English/Spanish)
    - Learning accommodations (autism, dyslexia, ADHD, etc.)
    - Detailed source references
    - Accessibility features
    """
    try:
        # Get child with all preferences
        result = await db.execute(
            select(Child).where(Child.id == message.child_id)
        )
        child = result.scalar_one_or_none()

        if not child or not child.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found or inactive"
            )

        # Get child's preferences
        language = getattr(child, 'preferred_language', 'en')
        accommodations = getattr(child, 'learning_accommodations', None)
        reading_level = getattr(child, 'reading_level', None) or child.grade_level
        enable_tts = getattr(child, 'enable_text_to_speech', False)

        # Get or create conversation
        conversation = None
        if message.conversation_id:
            result = await db.execute(
                select(DBConversation).where(
                    DBConversation.id == message.conversation_id,
                    DBConversation.child_id == message.child_id
                )
            )
            conversation = result.scalar_one_or_none()

        if not conversation:
            title = message.text[:50] + "..." if len(message.text) > 50 else message.text
            conversation = DBConversation(
                child_id=message.child_id,
                title=title,
                folder="General",
                message_count=0,
                total_depth_reached=1
            )
            db.add(conversation)
            await db.flush()

        # Save user message
        user_msg = DBMessage(
            conversation_id=conversation.id,
            role="user",
            content=message.text,
            depth_level=message.current_depth
        )
        db.add(user_msg)
        await db.flush()

        # Get Nia's response with all accommodations
        rag = get_rag_service()
        result = rag.query(
            question=message.text,
            grade_level=child.grade_level,
            depth_level=message.current_depth,
            child_age=None,  # Calculate if needed
            language=language,
            accommodations=accommodations,
            reading_level=reading_level
        )

        # Format answer
        formatted_answer = format_answer_with_depth(
            result["answer"],
            message.current_depth,
            language
        )

        # Build detailed source references with URLs
        source_references = []
        for idx, s in enumerate(result.get("sources", []), 1):
            source_ref = SourceReference(
                title=f"Web Search Result {idx}" if language == "en" else f"Resultado de Búsqueda {idx}",
                type="web_search",
                query=s.get("query", ""),
                citation_number=idx,
                verified=True
            )
            source_references.append(source_ref)

        # Determine complexity level based on accommodations
        if accommodations and "simplified_language" in accommodations:
            complexity_level = "simplified"
        elif message.current_depth >= 3:
            complexity_level = "advanced"
        else:
            complexity_level = "standard"

        # Source labeling
        used_web = result.get("used_web_search", False)
        if language == "es":
            source_type = "búsqueda_web" if used_web else "conocimiento_general"
            source_label = "🌐 De la web" if used_web else "ℹ️ De lo que sé"
        else:
            source_type = "web_search" if used_web else "general_knowledge"
            source_label = "🌐 From the web" if used_web else "ℹ️ From what I know"

        # Generate follow-up questions
        max_depth_reached = message.current_depth >= 3
        follow_up_offered = not max_depth_reached
        follow_up_questions = generate_follow_up_questions(
            message.current_depth,
            language
        ) if follow_up_offered else []

        # Save AI message
        ai_msg = DBMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=formatted_answer,
            model_used=result["model_used"],
            source_type=source_type,
            sources=[s.dict() for s in source_references],
            depth_level=message.current_depth
        )
        db.add(ai_msg)

        # Update metadata
        conversation.message_count += 2
        conversation.updated_at = datetime.utcnow()
        if message.current_depth > conversation.total_depth_reached:
            conversation.total_depth_reached = message.current_depth

        child.last_active = datetime.utcnow()

        await db.commit()
        await db.refresh(ai_msg)

        logger.info(
            f"✅ Message processed for child {message.child_id}, "
            f"lang={language}, accommodations={accommodations}"
        )

        return MessageResponse(
            message_id=str(ai_msg.id),
            conversation_id=conversation.id,
            text=formatted_answer,
            tutoring_depth_level=message.current_depth,
            follow_up_offered=follow_up_offered,
            follow_up_questions=follow_up_questions,
            source_references=source_references,
            source_type=source_type,
            source_label=source_label,
            model_used=result["model_used"],
            max_depth_reached=max_depth_reached,
            language=language,
            has_text_to_speech=enable_tts,
            complexity_level=complexity_level
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing your message"
        )


# ==================== Feedback Endpoint ====================

@router.post("/feedback", response_model=MessageFeedbackResponse)
async def submit_feedback(
    feedback: MessageFeedbackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback on a message (helpful/not helpful button)
    This helps improve Nia's responses over time
    """
    try:
        # Verify message exists
        result = await db.execute(
            select(DBMessage).where(DBMessage.id == feedback.message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        # Create feedback record
        feedback_record = MessageFeedback(
            message_id=feedback.message_id,
            child_id=feedback.child_id,
            is_helpful=feedback.is_helpful,
            feedback_type=feedback.feedback_type,
            feedback_text=feedback.feedback_text
        )

        db.add(feedback_record)
        await db.commit()

        logger.info(
            f"📊 Feedback received: message={feedback.message_id}, "
            f"helpful={feedback.is_helpful}, type={feedback.feedback_type}"
        )

        return MessageFeedbackResponse(
            success=True,
            message="Thank you for your feedback! This helps Nia learn and improve."
                   if feedback.is_helpful
                   else "Thank you for letting us know. We'll work on improving this."
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting feedback"
        )
