# Add these new models to your existing models.py file

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

# Add to existing models.py after your current models:

class FeedbackType(enum.Enum):
    """Types of feedback"""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INAPPROPRIATE = "inappropriate"
    TOO_COMPLEX = "too_complex"
    TOO_SIMPLE = "too_simple"

class MessageFeedback(Base):
    """Feedback on AI responses"""
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)

    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    feedback_text = Column(Text, nullable=True)  # Optional detailed feedback

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Language(enum.Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"

class LearningAccommodation(enum.Enum):
    """Types of learning accommodations"""
    AUTISM_SUPPORT = "autism_support"
    DYSLEXIA_SUPPORT = "dyslexia_support"
    ADHD_SUPPORT = "adhd_support"
    VISUAL_LEARNER = "visual_learner"
    SIMPLIFIED_LANGUAGE = "simplified_language"
    EXTRA_TIME = "extra_time"
    REDUCED_COMPLEXITY = "reduced_complexity"

# Update the Child model to include these new fields:
# Add these columns to your existing Child model:

class ChildEnhanced(Base):
    """Enhanced child profile with accessibility features"""
    __tablename__ = "children_enhanced"

    # ... existing fields ...

    # Language preference
    preferred_language = Column(SQLEnum(Language), default=Language.ENGLISH, nullable=False)

    # Learning accommodations (stored as JSON array)
    learning_accommodations = Column(JSON, nullable=True)  # List of LearningAccommodation values

    # Reading level (may differ from grade level)
    reading_level = Column(String, nullable=True)

    # Sensory preferences for autism support
    reduce_visual_complexity = Column(Boolean, default=False)
    use_literal_language = Column(Boolean, default=False)
    provide_structure_cues = Column(Boolean, default=False)

    # Text-to-speech preference
    enable_text_to_speech = Column(Boolean, default=False)
