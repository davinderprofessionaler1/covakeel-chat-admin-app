from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request
from typing import AsyncGenerator
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "rag_chatbot")

class MongoDB:
    client: AsyncIOMotorClient = None

mongodb = MongoDB()

def get_client() -> AsyncIOMotorClient:
    if not mongodb.client:
        mongodb.client = AsyncIOMotorClient(MONGODB_URI)
    return mongodb.client

def get_db():
    client = get_client()
    return client[MONGODB_DB] 