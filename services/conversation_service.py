from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Conversation, Message, Child
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        child_id: int,
        title: str = "New Conversation",
        folder: str = "General"
    ) -> Conversation:
        """Create a new conversation for a child"""
        conversation = Conversation(
            child_id=child_id,
            title=title,
            folder=folder,
            message_count=0,
            total_depth_reached=1
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        logger.info(f"Created conversation {conversation.id} for child {child_id}")
        return conversation

    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID"""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_child_conversations(
        self,
        child_id: int,
        folder: Optional[str] = None
    ) -> List[Conversation]:
        """Get all conversations for a child, optionally filtered by folder"""
        query = select(Conversation).where(Conversation.child_id == child_id)

        if folder:
            query = query.where(Conversation.folder == folder)

        query = query.order_by(Conversation.updated_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        source_type: Optional[str] = None,
        sources: Optional[List[Dict]] = None,
        depth_level: int = 1,
        model_used: Optional[str] = None
    ) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            source_type=source_type,
            sources=sources,
            depth_level=depth_level,
            model_used=model_used
        )
        self.db.add(message)

        # Update conversation metadata
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.message_count += 1
            conversation.updated_at = datetime.utcnow()
            if depth_level > conversation.total_depth_reached:
                conversation.total_depth_reached = depth_level

        await self.db.commit()
        await self.db.refresh(message)

        logger.info(f"Added {role} message to conversation {conversation_id}")
        return message

    async def get_conversation_messages(
        self,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get all messages in a conversation"""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_conversation_title(
        self,
        conversation_id: int,
        title: str
    ) -> Optional[Conversation]:
        """Update a conversation's title"""
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(conversation)
            logger.info(f"Updated conversation {conversation_id} title to: {title}")
        return conversation

    async def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages"""
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            await self.db.delete(conversation)
            await self.db.commit()
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False
