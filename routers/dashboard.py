from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import List, Dict
import logging
from database import get_db
from models import User, Child, Conversation, Message
from auth import get_current_active_parent

router = APIRouter()
logger = logging.getLogger(__name__)

class DashboardOverview(BaseModel):
    total_children: int
    active_children: int
    total_conversations: int
    total_messages: int
    recent_activity: List[Dict]

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(current_user: User = Depends(get_current_active_parent), db: AsyncSession = Depends(get_db)):
    total_children = (await db.execute(select(func.count(Child.id)).where(Child.parent_id == current_user.id))).scalar() or 0
    active_children = (await db.execute(select(func.count(Child.id)).where(Child.parent_id == current_user.id).where(Child.is_active == True))).scalar() or 0
    total_convs = (await db.execute(select(func.count(Conversation.id)).join(Child).where(Child.parent_id == current_user.id))).scalar() or 0
    total_msgs = (await db.execute(select(func.count(Message.id)).join(Conversation).join(Child).where(Child.parent_id == current_user.id))).scalar() or 0
    
    recent = await db.execute(select(Conversation, Child).join(Child).where(Child.parent_id == current_user.id).order_by(desc(Conversation.updated_at)).limit(10))
    recent_activity = [{"conversation_id": c.id, "child_name": ch.first_name, "title": c.title, "message_count": c.message_count, "last_updated": c.updated_at.isoformat()} for c, ch in recent]
    
    return {"total_children": total_children, "active_children": active_children, "total_conversations": total_convs, "total_messages": total_msgs, "recent_activity": recent_activity}
