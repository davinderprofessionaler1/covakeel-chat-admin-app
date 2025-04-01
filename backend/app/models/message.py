from typing import Optional
from datetime import datetime
from bson import ObjectId

class Message:
    def __init__(self, conversationId: ObjectId, sender: str, text: str, createdAt: Optional[datetime] = None, _id: Optional[ObjectId] = None):
        self._id = _id
        self.conversationId = conversationId
        self.sender = sender
        self.text = text
        self.createdAt = createdAt or datetime.utcnow() 