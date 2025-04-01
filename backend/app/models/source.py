from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

class Source:
    def __init__(self, messageId: ObjectId, filename: str, content: str, metadata: Optional[Dict[str, Any]] = None, createdAt: Optional[datetime] = None, _id: Optional[ObjectId] = None):
        self._id = _id
        self.messageId = messageId
        self.filename = filename
        self.content = content
        self.metadata = metadata
        self.createdAt = createdAt or datetime.utcnow() 