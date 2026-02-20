from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.communication import Communication, InitiatorLog
from backend.core.communication.service import get_message, get_chain, get_initiators

router = APIRouter(prefix="/communications", tags=["communications"])

@router.get("/initiators", response_model=List[InitiatorLog])
async def list_initiators():
    """List all conversation-starting messages (rows in initiator_log)."""
    try:
        return get_initiators()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{com_id}", response_model=Communication)
async def read_message(com_id: str):
    """Get the full raw content and metadata of a single message by com_id."""
    try:
        message = get_message(com_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Message not found")
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{com_id}/chain", response_model=List[Communication])
async def read_chain(com_id: str):
    """Retrieve the complete ordered chain of messages starting from the conversation root that contains the given com_id."""
    try:
        chain = get_chain(com_id)
        if not chain:
            raise HTTPException(status_code=404, detail="Chain not found or invalid com_id")
        return chain
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
