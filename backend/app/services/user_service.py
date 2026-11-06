from app.db.mongodb import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.hashing import hash_password
from bson import ObjectId
from typing import Optional
from datetime import datetime

async def create_user(user_create: UserCreate):
    db = get_db()
    user_dict = user_create.dict()
    user_dict["hashed_password"] = hash_password(user_dict.pop("password"))
    user_dict["createdAt"] = datetime.utcnow()
    user_dict["email"] = user_dict.get("email")
    result = await db["users"].insert_one(user_dict)
    return str(result.inserted_id)

async def get_user_by_username(username: str) -> Optional[User]:
    db = get_db()
    data = await db["users"].find_one({"username": username})
    if data:
        return User(**data)
    return None

async def get_user_by_id(user_id: str) -> Optional[User]:
    db = get_db()
    data = await db["users"].find_one({"_id": ObjectId(user_id)})
    if data:
        return User(**data)
    return None

async def update_user(user_id: str, user_update: UserUpdate):
    db = get_db()
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if v is not None}
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    return await get_user_by_id(user_id)

async def delete_user(user_id: str):
    db = get_db()
    await db["users"].delete_one({"_id": ObjectId(user_id)})


async def get_user_by_login(identifier: str) -> Optional[User]:
    """Accept existing usernames and the email address shown by the new design."""
    import re
    db = get_db()
    identifier = identifier.strip()
    data = await db["users"].find_one({"$or": [
        {"username": identifier},
        {"email": {"$regex": "^" + re.escape(identifier) + "$", "$options": "i"}},
    ]})
    return User(**data) if data else None
