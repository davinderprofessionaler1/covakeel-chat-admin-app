from typing import Optional
from datetime import datetime
from bson import ObjectId

class Conversation:
    def __init__(self, userId: ObjectId, title: Optional[str] = None, createdAt: Optional[datetime] = None, updatedAt: Optional[datetime] = None, _id: Optional[ObjectId] = None):
        self._id = _id
        self.userId = userId
        self.title = title
        self.createdAt = createdAt or datetime.utcnow()
        self.updatedAt = updatedAt or self.createdAt 