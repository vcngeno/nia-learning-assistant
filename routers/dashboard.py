"""Parent dashboard router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Dict
from datetime import datetime, timedelta

from database import get_db
from models import Parent, Child, Conversation, Message

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/{parent_id}")
async def get_dashboard(parent_id: int, db: Session = Depends(get_db)) -> Dict:
    """Get dashboard overview for parent"""
    try:
        # Get parent
        result = await db.execute(select(Parent).where(Parent.id == parent_id))
        parent = result.scalar_one_or_none()
    except AttributeError:
        parent = db.query(Parent).filter(Parent.id == parent_id).first()

    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    # Get children count
    try:
        result = await db.execute(
            select(func.count(Child.id)).where(Child.parent_id == parent_id)
        )
        children_count = result.scalar()
    except AttributeError:
        children_count = db.query(func.count(Child.id)).filter(Child.parent_id == parent_id).scalar()

    # Get total conversations
    try:
        result = await db.execute(
            select(func.count(Conversation.id))
            .join(Child)
            .where(Child.parent_id == parent_id)
        )
        total_conversations = result.scalar()
    except AttributeError:
        total_conversations = db.query(func.count(Conversation.id)).join(Child).filter(
            Child.parent_id == parent_id
        ).scalar()

    # Get recent activity
    week_ago = datetime.utcnow() - timedelta(days=7)
    try:
        result = await db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .join(Child)
            .where(Child.parent_id == parent_id)
            .where(Message.created_at >= week_ago)
        )
        messages_this_week = result.scalar()
    except AttributeError:
        messages_this_week = db.query(func.count(Message.id)).join(Conversation).join(Child).filter(
            Child.parent_id == parent_id,
            Message.created_at >= week_ago
        ).scalar()

    return {
        "parent_name": parent.full_name,
        "children_count": children_count,
        "total_conversations": total_conversations,
        "messages_this_week": messages_this_week
    }
