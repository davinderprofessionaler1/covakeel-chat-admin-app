"""Share expensive model resources while keeping conversation state per request."""
import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from app.core.config import CHROMA_DB_PATH

_rag_system = None
_executor = None
_init_lock = threading.Lock()


def get_rag_status():
    missing = []
    if not os.getenv("GOOGLE_API_KEY", "").strip():
        missing.append("Set GOOGLE_API_KEY in backend/.env and restart the backend")
    if not (CHROMA_DB_PATH / "chroma.sqlite3").is_file():
        missing.append("Build the Chroma index with scripts/index_local.py")
    return {"configured": not missing, "initialized": _rag_system is not None, "missing": missing}


def ensure_rag_configured():
    status = get_rag_status()
    if status["missing"]:
        raise RuntimeError("; ".join(status["missing"]))


def get_rag_system():
    global _rag_system
    ensure_rag_configured()
    with _init_lock:
        if _rag_system is None:
            from app.services.retrieval_service import ConversationalRAGSystem
            candidate = ConversationalRAGSystem(chroma_db_path=str(CHROMA_DB_PATH))
            if candidate.vector_store._collection.count() == 0:
                raise RuntimeError("The Chroma collection is empty. Run scripts/index_local.py")
            _rag_system = candidate
    return _rag_system


def get_executor():
    global _executor
    with _init_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


def ask_sync(question: str, chat_history=None):
    return get_rag_system().ask(question, chat_history)


async def ask_async(question: str, chat_history=None):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_executor(), ask_sync, question, chat_history)


async def ask_stream(question: str, chat_history=None):
    # This preserves the original plain-text client protocol. Model token streaming
    # can be added separately; do not add artificial delays to a completed answer.
    response = await ask_async(question, chat_history)
    yield response["answer"]


def shutdown_executor():
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None
