from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SourceCreate(BaseModel):
    messageId: str
    filename: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SourceRead(BaseModel):
    id: str
    messageId: str
    filename: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    createdAt: datetime 