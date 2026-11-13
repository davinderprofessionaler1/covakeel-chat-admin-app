"""Share expensive model resources while keeping conversation state per request."""
import asyncio
import os
import threading
from concurrent.futures import ThreadPoolExecutor

_rag_system = None
_executor = None
_init_lock = threading.Lock()


def get_rag_status():
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        missing.append("Set ANTHROPIC_API_KEY in backend/.env and restart the backend")
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
            from app.core.config import CHROMA_DB_PATH
            _rag_system = ConversationalRAGSystem(chroma_db_path=str(CHROMA_DB_PATH))
    return _rag_system


def get_executor():
    global _executor
    with _init_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


def ask_sync(question: str, chat_history=None):
    system = get_rag_system()
    if system.vector_store._collection.count() == 0:
        return {"question": question, "answer": "I could not find the answer in the indexed documents.", "source_documents": []}
    return system.ask(question, chat_history)


async def ask_async(question: str, chat_history=None):
    from app.services import legal_change_service
    change = await legal_change_service.find_change(question)
    if change:
        return legal_change_service.comparison_answer(change, question)
    if legal_change_service.CURRENT_OR_COMPARISON.search(question):
        return legal_change_service.unverified_answer(question)
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
