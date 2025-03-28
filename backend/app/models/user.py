from typing import Optional
from datetime import datetime
from bson import ObjectId

class User:
    def __init__(self, username: str, hashed_password: str, email: Optional[str] = None, createdAt: Optional[datetime] = None, _id: Optional[ObjectId] = None):
        self._id = _id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.createdAt = createdAt or datetime.utcnow() 