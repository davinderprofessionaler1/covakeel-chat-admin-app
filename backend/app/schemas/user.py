from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None

class UserRead(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    createdAt: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=32)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6) 