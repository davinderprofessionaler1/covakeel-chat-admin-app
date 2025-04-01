from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageCreate(BaseModel):
    conversationId: str
    sender: str
    text: str

class MessageRead(BaseModel):
    id: str
    conversationId: str
    sender: str
    text: str
    createdAt: datetime 