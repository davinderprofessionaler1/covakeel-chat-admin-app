from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request
from typing import AsyncGenerator
from app.core.config import MONGODB_URI, MONGODB_DB

class MongoDB:
    client: AsyncIOMotorClient = None

mongodb = MongoDB()

def get_client() -> AsyncIOMotorClient:
    if not mongodb.client:
        mongodb.client = AsyncIOMotorClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return mongodb.client

def get_db():
    client = get_client()
    return client[MONGODB_DB]
