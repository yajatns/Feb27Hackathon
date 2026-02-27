"""Chat persistence — save and retrieve query conversations."""

import json
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import ChatMessage

router = APIRouter()


@router.get("/chats")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all unique chat sessions with last message preview."""
    result = await db.execute(
        select(ChatMessage).order_by(ChatMessage.created_at.desc())
    )
    messages = result.scalars().all()

    sessions = {}
    for msg in messages:
        if msg.session_id not in sessions:
            sessions[msg.session_id] = {
                "session_id": msg.session_id,
                "last_message": msg.content[:100],
                "message_count": 0,
                "created_at": str(msg.created_at),
            }
        sessions[msg.session_id]["message_count"] += 1

    return list(sessions.values())


@router.get("/chats/{session_id}")
async def get_chat(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get all messages for a chat session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "tools_used": json.loads(msg.tools_used) if msg.tools_used else [],
            "reasoning": msg.reasoning,
            "created_at": str(msg.created_at),
        }
        for msg in messages
    ]


async def save_message(db: AsyncSession, session_id: str, role: str, content: str,
                       tools_used: list[str] | None = None, reasoning: str | None = None):
    """Save a chat message to the database."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tools_used=json.dumps(tools_used) if tools_used else None,
        reasoning=reasoning,
    )
    db.add(msg)
    await db.flush()
    return msg
