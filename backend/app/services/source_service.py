from app.db.mongodb import get_db
from app.models.source import Source
from app.schemas.source import SourceCreate
from bson import ObjectId
from typing import List
from datetime import datetime

async def create_source(source_create: SourceCreate):
    db = get_db()
    doc = {
        "messageId": ObjectId(source_create.messageId),
        "filename": source_create.filename,
        "content": source_create.content,
        "metadata": source_create.metadata,
        "createdAt": datetime.utcnow()
    }
    result = await db["sources"].insert_one(doc)
    return str(result.inserted_id)

async def list_sources_by_message(msg_id: str) -> List[Source]:
    db = get_db()
    cursor = db["sources"].find({"messageId": ObjectId(msg_id)})
    return [Source(**doc) async for doc in cursor]

async def delete_source(source_id: str):
    db = get_db()
    await db["sources"].delete_one({"_id": ObjectId(source_id)}) 