from app.db.mongodb import get_db
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from bson import ObjectId
from typing import Optional, List
from datetime import datetime

async def create_conversation(user_id: str, conv_create: ConversationCreate):
    db = get_db()
    doc = {
        "userId": ObjectId(user_id),
        "title": conv_create.title or "Untitled",
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    result = await db["conversations"].insert_one(doc)
    return str(result.inserted_id)

async def get_conversation_by_id(conv_id: str) -> Optional[Conversation]:
    db = get_db()
    data = await db["conversations"].find_one({"_id": ObjectId(conv_id)})
    if data:
        return Conversation(**data)
    return None

async def list_conversations_by_user(user_id: str) -> List[Conversation]:
    db = get_db()
    cursor = db["conversations"].find({"userId": ObjectId(user_id)}).sort("updatedAt", -1)
    return [Conversation(**doc) async for doc in cursor]

async def update_conversation(conv_id: str, conv_update: ConversationUpdate):
    db = get_db()
    update_data = {k: v for k, v in conv_update.dict(exclude_unset=True).items() if v is not None}
    update_data["updatedAt"] = datetime.utcnow()
    await db["conversations"].update_one({"_id": ObjectId(conv_id)}, {"$set": update_data})
    return await get_conversation_by_id(conv_id)

async def delete_conversation(conv_id: str):
    db = get_db()
    await db["conversations"].delete_one({"_id": ObjectId(conv_id)})
