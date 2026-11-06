from typing import Optional
from datetime import datetime
from bson import ObjectId

class User:
    def __init__(self, username: str, hashed_password: str, email: Optional[str] = None, createdAt: Optional[datetime] = None, _id: Optional[ObjectId] = None, name: Optional[str] = None, profile: Optional[dict] = None, is_admin: bool = False):
        self._id = _id
        self.username = username
        self.name = name
        self.profile = profile or {}
        self.email = email
        self.hashed_password = hashed_password
        self.createdAt = createdAt or datetime.utcnow()
        self.is_admin = is_admin
