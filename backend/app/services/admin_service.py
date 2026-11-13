"""Admin document registry and live Chroma updates.

The original three PDFs already exist in Chroma. Their manifest is imported
as registry entries once; later uploads can replace or remove them by filename.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading

import fitz
from bson import ObjectId
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import ADMIN_UPLOAD_DIR, CHROMA_DB_PATH
from app.db.mongodb import get_db
from app.services import rag_service


MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PAGES = 500
_index_lock = threading.Lock()


def public_document(doc):
    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "title": doc.get("title") or Path(doc["filename"]).stem.replace("_", " "),
        "sourceUrl": doc.get("source_url", ""),
        "status": doc["status"],
        "origin": doc.get("origin", "upload"),
        "pages": doc.get("pages", 0),
        "chunks": doc.get("chunks", 0),
        "size": doc.get("size", 0),
        "sha256": doc.get("sha256", ""),
        "error": doc.get("error"),
        "createdAt": doc["createdAt"].replace(tzinfo=timezone.utc).isoformat(),
    }


async def seed_documents():
    manifest_path = CHROMA_DB_PATH / "local_manifest.json"
    if not manifest_path.is_file():
        return
    try:
        sources = json.loads(manifest_path.read_text()).get("sources", [])
    except (ValueError, OSError):
        return
    now = datetime.utcnow()
    for item in sources:
        if not item.get("filename") or not item.get("sha256"):
            continue
        source_url = item.get("source_url") or item.get("source")
        metadata = {}
        if item.get("title"):
            metadata["title"] = item["title"]
        if source_url and source_url.startswith("https://"):
            metadata["source_url"] = source_url
        await get_db().admin_documents.update_one(
            {"_id": "seed:" + item["sha256"][:24]},
            {"$set": metadata, "$setOnInsert": {
                "filename": item["filename"], "sha256": item["sha256"],
                "status": "indexed", "origin": "starter", "size": 0,
                "pages": item.get("pages", 0), "chunks": item.get("chunks", 0),
                "createdAt": now, "updatedAt": now,
            }},
            upsert=True,
        )


def _discard_partial_upload(doc_id: str):
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    try:
        collection = client.get_collection("indian_law_acts")
    except Exception:
        return
    ids = collection.get(where={"document_id": doc_id}, include=["metadatas"])["ids"]
    if ids:
        collection.delete(ids=ids)


async def recover_interrupted_uploads():
    db = get_db()
    async for doc in db.admin_documents.find({"status": "processing"}):
        await asyncio.to_thread(_discard_partial_upload, str(doc["_id"]))
        await db.admin_documents.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "failed", "error": "Indexing was interrupted. Upload this PDF again.", "updatedAt": datetime.utcnow()}},
        )
        (ADMIN_UPLOAD_DIR / f"{doc['_id']}.pdf").unlink(missing_ok=True)


async def list_documents():
    cursor = get_db().admin_documents.find(
        {"status": {"$in": ["indexed", "processing", "failed"]}}
    ).sort("createdAt", -1)
    return [public_document(doc) async for doc in cursor]


def _index_pdf(path: Path, doc_id: str, filename: str, sha256: str, title: str, source_url: str):
    pages = []
    with fitz.open(path) as pdf:
        if pdf.page_count > MAX_PAGES:
            raise ValueError(f"PDF has more than {MAX_PAGES} pages")
        for number, page in enumerate(pdf, 1):
            content = page.get_text().strip()
            if content:
                metadata = {
                    "filename": filename, "source": f"admin-upload:{doc_id}",
                    "page": number, "language": "EN", "sha256": sha256,
                    "document_id": doc_id, "title": title,
                }
                if source_url:
                    metadata["source_url"] = source_url
                pages.append(Document(page_content=content, metadata=metadata))
    if not pages:
        raise ValueError("No selectable text found. Run OCR on scanned PDFs before upload")
    chunks = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500).split_documents(pages)
    if len(chunks) > 2000:
        raise ValueError("PDF creates too many chunks; split it into smaller documents")
    if title.endswith(" [OCR]"):
        for chunk in chunks:
            chunk.page_content = (
                "[OCR transcription; verify exact legal wording and figures in the linked official PDF.]\n"
                + chunk.page_content
            )
            chunk.metadata["text_quality"] = "OCR"
    ids = [f"{doc_id}:{i}" for i in range(len(chunks))]
    with _index_lock:
        store = rag_service.get_rag_system().vector_store
        old_ids = store._collection.get(where={"filename": filename}, include=["metadatas"])["ids"]
        try:
            for start in range(0, len(chunks), 100):
                store.add_documents(chunks[start:start + 100], ids=ids[start:start + 100])
            if old_ids:
                store._collection.delete(ids=old_ids)
        except Exception:
            inserted = store._collection.get(where={"document_id": doc_id}, include=["metadatas"])["ids"]
            if inserted:
                store._collection.delete(ids=inserted)
            raise
    return len(pages), len(chunks)


async def process_upload(doc_id: str):
    db = get_db()
    doc = await db.admin_documents.find_one({"_id": doc_id})
    if not doc or doc["status"] != "processing":
        return
    path = ADMIN_UPLOAD_DIR / f"{doc_id}.pdf"
    try:
        pages, chunks = await asyncio.to_thread(
            _index_pdf, path, doc_id, doc["filename"], doc["sha256"],
            doc["title"], doc.get("source_url", "")
        )
        now = datetime.utcnow()
        previous = [item async for item in db.admin_documents.find({
            "filename": doc["filename"], "status": "indexed", "_id": {"$ne": doc_id}
        }, {"_id": 1, "origin": 1})]
        await db.admin_documents.update_many(
            {"filename": doc["filename"], "status": "indexed", "_id": {"$ne": doc_id}},
            {"$set": {"status": "replaced", "updatedAt": now}},
        )
        await db.admin_documents.update_one(
            {"_id": doc_id},
            {"$set": {"status": "indexed", "pages": pages, "chunks": chunks, "updatedAt": now}},
        )
        for item in previous:
            if item.get("origin") == "upload":
                (ADMIN_UPLOAD_DIR / f"{item['_id']}.pdf").unlink(missing_ok=True)
    except Exception as exc:
        await db.admin_documents.update_one(
            {"_id": doc_id},
            {"$set": {"status": "failed", "error": str(exc)[:300], "updatedAt": datetime.utcnow()}},
        )
        path.unlink(missing_ok=True)


async def queue_upload(filename: str, data: bytes, title: str, source_url: str = ""):
    db = get_db()
    sha256 = hashlib.sha256(data).hexdigest()
    if await db.admin_documents.find_one({"filename": filename, "status": "processing"}):
        raise ValueError("This document is already processing")
    if await db.admin_documents.find_one({"sha256": sha256, "status": "indexed"}):
        raise ValueError("This PDF is already in the knowledge base")
    ADMIN_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    doc_id = str(ObjectId())
    path = ADMIN_UPLOAD_DIR / f"{doc_id}.pdf"
    path.write_bytes(data)
    now = datetime.utcnow()
    doc = {
        "_id": doc_id, "filename": filename, "title": title,
        "source_url": source_url, "sha256": sha256,
        "status": "processing", "origin": "upload", "size": len(data),
        "pages": 0, "chunks": 0, "createdAt": now, "updatedAt": now,
    }
    try:
        await db.admin_documents.insert_one(doc)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return public_document(doc)


def _remove_from_index(filename: str):
    with _index_lock:
        store = rag_service.get_rag_system().vector_store
        ids = store._collection.get(where={"filename": filename}, include=["metadatas"])["ids"]
        if ids:
            store._collection.delete(ids=ids)


async def delete_document(doc_id: str):
    db = get_db()
    doc = await db.admin_documents.find_one({"_id": doc_id, "status": {"$in": ["indexed", "failed"]}})
    if not doc:
        return False
    if doc["status"] == "indexed":
        await asyncio.to_thread(_remove_from_index, doc["filename"])
    await db.admin_documents.update_one(
        {"_id": doc_id}, {"$set": {"status": "deleted", "updatedAt": datetime.utcnow()}}
    )
    if doc["origin"] == "upload":
        (ADMIN_UPLOAD_DIR / f"{doc_id}.pdf").unlink(missing_ok=True)
    return True
