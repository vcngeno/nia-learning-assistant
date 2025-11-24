from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class ConsentType(enum.Enum):
    """Types of parental consent"""
    EMAIL_VERIFICATION = "email_verification"
    TERMS_ACCEPTANCE = "terms_acceptance"
    DATA_COLLECTION = "data_collection"
    MONITORING = "monitoring"

class User(Base):
    """Parent/Guardian accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    consent_records = relationship("ConsentRecord", back_populates="user")

class Child(Base):
    """Child profiles (COPPA compliant)"""
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    first_name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    grade_level = Column(String, nullable=False)

    # Language and learning preferences
    preferred_language = Column(String, default="en", nullable=False)  # 'en' or 'es'
    reading_level = Column(String, default="at grade level", nullable=True)
    learning_accommodations = Column(JSON, default=list, nullable=True)  # ['autism_support', 'dyslexia_support', etc.]

    pin_hash = Column(String, nullable=True)

    avatar_url = Column(String, nullable=True)
    learning_preferences = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    requires_supervision = Column(Boolean, default=True, nullable=False)
    content_filter_level = Column(String, default="strict", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)

    parent = relationship("User", back_populates="children")
    conversations = relationship("Conversation", back_populates="child", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="child")

class Session(Base):
    """User session tracking"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sessions")

class ConsentRecord(Base):
    """COPPA compliance - parental consent tracking"""
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    consent_type = Column(SQLEnum(ConsentType), nullable=False)
    granted = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="consent_records")

class Conversation(Base):
    """Chat conversations"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)
    folder = Column(String, default="General", nullable=False)
    topics = Column(JSON, nullable=True)

    message_count = Column(Integer, default=0, nullable=False)
    total_depth_reached = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    child = relationship("Child", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Individual messages in conversations"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)

    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    model_used = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    sources = Column(JSON, nullable=True)

    depth_level = Column(Integer, default=1, nullable=False)
    tutoring_depth_level = Column(Integer, default=1, nullable=False)  # Alias for depth_level
    has_curated_content = Column(Boolean, default=False, nullable=False)

    flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")

class UsageLog(Base):
    """Track child usage for analytics"""
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)

    session_duration_seconds = Column(Integer, nullable=True)
    messages_sent = Column(Integer, default=0)
    topics_explored = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    child = relationship("Child", back_populates="usage_logs")

class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)

    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Add these to the existing Child model in models.py:
# (Just add these lines to your Child class)

    # Language and accessibility features
    preferred_language = Column(String, default="en", nullable=False)  # 'en' or 'es'
    learning_accommodations = Column(JSON, nullable=True)
    reading_level = Column(String, nullable=True)

    # Autism/special needs support flags
    reduce_visual_complexity = Column(Boolean, default=False)
    use_literal_language = Column(Boolean, default=False)
    provide_structure_cues = Column(Boolean, default=False)
    enable_text_to_speech = Column(Boolean, default=False)


class MessageFeedback(Base):
    """Feedback on AI responses for continuous improvement"""
    __tablename__ = "message_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)

    is_helpful = Column(Boolean, nullable=False)
    feedback_type = Column(String, nullable=True)  # "too_complex", "too_simple", "inappropriate"
    feedback_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EducationalContent(Base):
    """Educational content documents"""
    __tablename__ = "educational_content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=False, index=True)  # math, science, history, etc.
    grade_level = Column(String, nullable=False, index=True)  # elementary, middle, high
    topic = Column(String, nullable=False, index=True)  # specific topic
    content = Column(Text, nullable=False)  # Full markdown content
    content_hash = Column(String, nullable=False)  # MD5 hash for change detection
    file_path = Column(String, unique=True, nullable=False)  # Path to source file
    word_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<EducationalContent(id={self.id}, title='{self.title}', subject='{self.subject}')>"
