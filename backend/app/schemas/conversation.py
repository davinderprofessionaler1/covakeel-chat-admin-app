from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationRead(BaseModel):
    id: str
    userId: str
    title: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

class ConversationUpdate(BaseModel):
    title: Optional[str] = None 