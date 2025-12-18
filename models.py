"""SQLAlchemy database models"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Parent(Base):
    """Parent/Guardian account"""
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")

class Child(Base):
    """Child profile"""
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    first_name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=False)
    grade_level = Column(String, nullable=False)
    hashed_pin = Column(String, nullable=False)
    preferred_language = Column(String, default="en")
    learning_accommodations = Column(JSON, nullable=True, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    progress_level = Column(String, default="at grade level")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Parent", back_populates="children")
    conversations = relationship("Conversation", back_populates="child", cascade="all, delete-orphan")

class Conversation(Base):
    """Conversation thread"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    title = Column(String, nullable=False)
    folder = Column(String, default="General")
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    child = relationship("Child", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Individual message in conversation"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
