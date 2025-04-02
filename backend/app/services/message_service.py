from app.db.mongodb import get_db
from app.models.message import Message
from app.schemas.message import MessageCreate
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

async def create_message(msg_create: MessageCreate):
    db = get_db()
    doc = {
        "conversationId": ObjectId(msg_create.conversationId),
        "sender": msg_create.sender,
        "text": msg_create.text,
        "createdAt": datetime.utcnow()
    }
    result = await db["messages"].insert_one(doc)
    return str(result.inserted_id)

async def get_message_by_id(msg_id: str) -> Optional[Message]:
    db = get_db()
    data = await db["messages"].find_one({"_id": ObjectId(msg_id)})
    if data:
        return Message(**data)
    return None

async def list_messages_by_conversation(conv_id: str) -> List[Message]:
    db = get_db()
    cursor = db["messages"].find({"conversationId": ObjectId(conv_id)}).sort("createdAt", 1)
    return [Message(**doc) async for doc in cursor]

async def delete_message(msg_id: str):
    db = get_db()
    await db["messages"].delete_one({"_id": ObjectId(msg_id)}) 