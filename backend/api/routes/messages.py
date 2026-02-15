from fastapi import APIRouter, HTTPException, Query
from typing import List

from backend.models.message import MessageResponse, MessageCreate
from backend.services.message_service import (
    get_all_messages,
    get_recent_messages,
    save_message,
    clear_all_messages
)

router = APIRouter(prefix="/messages", tags=["messages"])

@router.get("", response_model=List[MessageResponse])
async def list_messages(limit: int = Query(100, ge=1, le=1000)):
    """Retrieve all messages with an optional limit."""
    try:
        messages = get_all_messages(limit)
        return [
            MessageResponse(
                id=msg.id,
                sender=msg.sender,
                content=msg.content,
                timestamp=msg.timestamp.isoformat()
            ) for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent", response_model=List[MessageResponse])
async def list_recent_messages(limit: int = Query(50, ge=1, le=100)):
    """Get the most recent messages."""
    try:
        messages = get_recent_messages(limit)
        return [
            MessageResponse(
                id=msg.id,
                sender=msg.sender,
                content=msg.content,
                timestamp=msg.timestamp.isoformat()
            ) for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=MessageResponse)
async def create_message(message: MessageCreate):
    """Save a new message."""
    try:
        saved_msg = save_message(message)
        return MessageResponse(
            id=saved_msg.id,
            sender=saved_msg.sender,
            content=saved_msg.content,
            timestamp=saved_msg.timestamp.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("", status_code=204)
async def delete_all_messages():
    """Clear all messages (for testing/development)."""
    try:
        clear_all_messages()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
