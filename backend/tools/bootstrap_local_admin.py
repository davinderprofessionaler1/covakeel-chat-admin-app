#!/usr/bin/env python3
"""Create the local CoVakeel admin login without contacting the live VPS."""

from datetime import datetime
from pathlib import Path
import secrets
import sys
from urllib.parse import urlparse

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import MONGODB_DB, MONGODB_URI
from app.utils.hashing import hash_password


def main():
    parsed = urlparse(MONGODB_URI)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("This bootstrap tool only runs against local MongoDB")
    db = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)[MONGODB_DB]
    email = "covakeel@gmail.com"
    user = db.users.find_one({"email": email})
    if user:
        db.users.update_one({"_id": user["_id"]}, {"$set": {"is_admin": True}})
        print("Existing local account promoted:", email)
        return
    password = secrets.token_urlsafe(24)
    db.users.insert_one({
        "username": "covakeel_admin",
        "email": email,
        "name": "CoVakeel Admin",
        "hashed_password": hash_password(password),
        "is_admin": True,
        "profile": {},
        "createdAt": datetime.utcnow(),
    })
    path = Path(__file__).resolve().parents[2] / ".local" / "admin-access.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(f"Local admin URL: http://127.0.0.1:8081/admin/\nEmail: {email}\nPassword: {password}\n")
    print("Created local admin login. Credentials are in", path)


if __name__ == "__main__":
    main()
