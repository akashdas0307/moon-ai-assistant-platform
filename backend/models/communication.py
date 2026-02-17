from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CommunicationCreate(BaseModel):
    sender: str
    recipient: str
    raw_content: str
    initiator_com_id: Optional[str] = None   # None for first message in chain

class Communication(BaseModel):
    com_id: str
    sender: str
    recipient: str
    timestamp: datetime
    raw_content: str
    initiator_com_id: Optional[str] = None
    exitor_com_id: Optional[str] = None
    is_condensed: bool = False
    condensed_summary: Optional[str] = None

    model_config = {"from_attributes": True}

class InitiatorLog(BaseModel):
    id: int
    com_id: str
    timestamp: datetime

    model_config = {"from_attributes": True}
