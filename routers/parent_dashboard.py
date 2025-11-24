"""
Parent Dashboard Router
Provides analytics and controls for parents
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_db
from models import Parent, Child, Conversation, Message
from routers.auth import get_current_parent

router = APIRouter(prefix="/parent", tags=["Parent Dashboard"])
logger = logging.getLogger("routers.parent_dashboard")

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent)
):
    """Get overview stats for parent dashboard"""

    # Get all children
    children = db.query(Child).filter(Child.parent_id == current_parent.id).all()
    child_ids = [c.id for c in children]

    # Total conversations
    total_conversations = db.query(Conversation).filter(
        Conversation.child_id.in_(child_ids)
    ).count()

    # Total messages
    total_messages = db.query(Message).join(Conversation).filter(
        Conversation.child_id.in_(child_ids)
    ).count()

    # Topics covered (unique folders)
    topics = db.query(Conversation.folder).filter(
        Conversation.child_id.in_(child_ids),
        Conversation.folder.isnot(None)
    ).distinct().all()

    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = db.query(
        func.date(Message.created_at).label('date'),
        func.count(Message.id).label('count')
    ).join(Conversation).filter(
        Conversation.child_id.in_(child_ids),
        Message.created_at >= week_ago
    ).group_by(func.date(Message.created_at)).all()

    return {
        "total_children": len(children),
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "topics_covered": [t[0] for t in topics if t[0]],
        "recent_activity": [
            {"date": str(a.date), "messages": a.count}
            for a in recent_activity
        ]
    }

@router.get("/dashboard/child/{child_id}")
async def get_child_analytics(
    child_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent)
):
    """Get detailed analytics for specific child"""

    # Verify child belongs to parent
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == current_parent.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Time range
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get conversations
    conversations = db.query(Conversation).filter(
        Conversation.child_id == child_id,
        Conversation.created_at >= start_date
    ).order_by(desc(Conversation.updated_at)).all()

    # Topics breakdown
    topics_query = db.query(
        Conversation.folder,
        func.count(Conversation.id).label('count')
    ).filter(
        Conversation.child_id == child_id,
        Conversation.folder.isnot(None)
    ).group_by(Conversation.folder).all()

    topics_breakdown = {t.folder: t.count for t in topics_query}

    # Message count per day
    daily_activity = db.query(
        func.date(Message.created_at).label('date'),
        func.count(Message.id).label('count')
    ).join(Conversation).filter(
        Conversation.child_id == child_id,
        Message.created_at >= start_date
    ).group_by(func.date(Message.created_at)).all()

    # Average messages per conversation
    avg_messages = db.query(
        func.avg(
            db.query(func.count(Message.id))
            .filter(Message.conversation_id == Conversation.id)
            .correlate(Conversation)
            .scalar_subquery()
        )
    ).filter(Conversation.child_id == child_id).scalar() or 0

    return {
        "child": {
            "id": child.id,
            "name": child.first_name,
            "nickname": child.nickname,
            "grade_level": child.grade_level
        },
        "total_conversations": len(conversations),
        "topics_breakdown": topics_breakdown,
        "daily_activity": [
            {"date": str(a.date), "messages": a.count}
            for a in daily_activity
        ],
        "avg_messages_per_conversation": round(float(avg_messages), 1),
        "recent_conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "folder": conv.folder,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages)
            }
            for conv in conversations[:10]
        ]
    }

@router.get("/dashboard/child/{child_id}/conversations")
async def get_all_child_conversations(
    child_id: int,
    folder: Optional[str] = None,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent)
):
    """Get all conversations for a child with optional folder filter"""

    # Verify child belongs to parent
    child = db.query(Child).filter(
        Child.id == child_id,
        Child.parent_id == current_parent.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    query = db.query(Conversation).filter(Conversation.child_id == child_id)

    if folder:
        query = query.filter(Conversation.folder == folder)

    conversations = query.order_by(desc(Conversation.updated_at)).all()

    return {
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title,
                "folder": conv.folder,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": len(conv.messages)
            }
            for conv in conversations
        ]
    }

@router.get("/dashboard/conversation/{conversation_id}/full")
async def get_full_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_parent: Parent = Depends(get_current_parent)
):
    """Get full conversation with all messages for parent review"""

    # Get conversation and verify access
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify parent owns the child
    child = db.query(Child).filter(
        Child.id == conversation.child_id,
        Child.parent_id == current_parent.id
    ).first()

    if not child:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "folder": conversation.folder,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        },
        "child": {
            "id": child.id,
            "name": child.first_name
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "source_label": msg.source_label,
                "created_at": msg.created_at.isoformat(),
                "feedback": msg.feedback
            }
            for msg in conversation.messages
        ]
    }
