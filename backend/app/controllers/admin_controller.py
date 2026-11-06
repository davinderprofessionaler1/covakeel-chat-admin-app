"""Admin-only read views and document management for the local dashboard."""

import os
import re
import shutil
from urllib.parse import urlparse

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status

from app.core.config import ADMIN_UPLOAD_DIR, CHROMA_DB_PATH
from app.core.security import get_current_admin
from app.db.mongodb import get_db
from app.services import admin_service, rag_service


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get("/overview")
async def overview():
    db = get_db()
    documents = await admin_service.list_documents()
    active = [item for item in documents if item["status"] == "indexed"]
    return {
        "users": await db.users.count_documents({}),
        "conversations": await db.conversations.count_documents({}),
        "messages": await db.messages.count_documents({}),
        "documents": len(active),
        "indexedChunks": sum(item["chunks"] for item in active),
        "processing": sum(item["status"] == "processing" for item in documents),
        "rag": rag_service.get_rag_status(),
    }


@router.get("/documents")
async def documents():
    return await admin_service.list_documents()


@router.post("/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    request: Request,
    background_tasks: BackgroundTasks,
    filename: str = Query(..., min_length=1, max_length=160),
    title: str | None = Query(None, max_length=180),
    source_url: str | None = Query(None, max_length=500),
):
    filename = filename.strip()
    if (
        filename != filename.replace("\\", "/").split("/")[-1]
        or not filename.lower().endswith(".pdf")
        or re.search(r"[\x00-\x1f\x7f]", filename)
    ):
        raise HTTPException(status_code=400, detail="Use a plain .pdf filename")
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/pdf":
        raise HTTPException(status_code=415, detail="Upload a PDF file")
    title = (title or filename[:-4].replace("_", " ")).strip()
    if not title or re.search(r"[\x00-\x1f\x7f]", title):
        raise HTTPException(status_code=400, detail="Use a plain document title")
    source_url = (source_url or "").strip()
    if source_url:
        parsed = urlparse(source_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise HTTPException(status_code=400, detail="Source URL must be HTTPS")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > admin_service.MAX_PDF_BYTES:
            raise HTTPException(status_code=413, detail="PDF must be 20 MB or smaller")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")
    try:
        doc = await admin_service.queue_upload(filename, bytes(data), title, source_url)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    background_tasks.add_task(admin_service.process_upload, doc["id"])
    return doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str):
    if not await admin_service.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")


@router.get("/users")
async def users(limit: int = Query(100, ge=1, le=200)):
    cursor = get_db().users.find({}, {
        "username": 1, "email": 1, "name": 1, "createdAt": 1, "is_admin": 1
    }).sort("createdAt", -1).limit(limit)
    result = []
    async for user in cursor:
        result.append({
            "id": str(user["_id"]), "username": user["username"],
            "email": user.get("email"), "name": user.get("name"),
            "isAdmin": user.get("is_admin", False),
            "createdAt": user.get("createdAt").isoformat() if user.get("createdAt") else None,
        })
    return result


@router.get("/conversations")
async def conversations(limit: int = Query(100, ge=1, le=200)):
    cursor = get_db().conversations.find({}, {
        "title": 1, "userId": 1, "createdAt": 1, "updatedAt": 1
    }).sort("updatedAt", -1).limit(limit)
    rows = [item async for item in cursor]
    user_ids = [item["userId"] for item in rows if isinstance(item.get("userId"), ObjectId)]
    names = {}
    async for user in get_db().users.find({"_id": {"$in": user_ids}}, {"username": 1, "email": 1}):
        names[str(user["_id"])] = user.get("email") or user.get("username")
    return [{
        "id": str(item["_id"]), "title": item.get("title") or "Untitled",
        "owner": names.get(str(item.get("userId")), "Unknown user"),
        "createdAt": item.get("createdAt").isoformat() if item.get("createdAt") else None,
        "updatedAt": item.get("updatedAt").isoformat() if item.get("updatedAt") else None,
    } for item in rows]


@router.get("/health")
async def health():
    try:
        await get_db().command("ping")
        database = "connected"
    except Exception:
        database = "unavailable"
    documents = await admin_service.list_documents()
    disk = shutil.disk_usage(CHROMA_DB_PATH)
    return {
        "database": database,
        "rag": rag_service.get_rag_status(),
        "indexedDocuments": sum(item["status"] == "indexed" for item in documents),
        "processingDocuments": sum(item["status"] == "processing" for item in documents),
        "failedDocuments": sum(item["status"] == "failed" for item in documents),
        "indexedChunks": sum(item["chunks"] for item in documents if item["status"] == "indexed"),
        "freeDiskGb": round(disk.free / (1024 ** 3), 1),
    }


@router.get("/settings")
async def settings(admin=Depends(get_current_admin)):
    return {
        "adminEmail": admin.email,
        "model": os.getenv("GOOGLE_MODEL", "gemini-3.5-flash-lite"),
        "maxPdfMb": admin_service.MAX_PDF_BYTES // (1024 * 1024),
        "uploadDirectory": str(ADMIN_UPLOAD_DIR),
        "collection": "indian_law_acts",
    }
