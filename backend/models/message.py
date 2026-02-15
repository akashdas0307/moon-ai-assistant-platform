from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    sender: str
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: str  # ISO string for API responses
