from app.services.retrieval_service import ConversationalRAGSystem
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

# Singleton instance
_rag_system = None
_executor = None

def get_rag_system():
    global _rag_system
    if _rag_system is None:
        _rag_system = ConversationalRAGSystem()
    return _rag_system

def get_executor():
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor

def ask_sync(question: str, chat_history=None):
    rag = get_rag_system()
    return rag.ask(question)

async def ask_async(question: str, chat_history=None):
    """Async wrapper for the synchronous ask method"""
    rag = get_rag_system()
    loop = asyncio.get_event_loop()
    executor = get_executor()
    
    # Run the synchronous method in a thread pool
    response = await loop.run_in_executor(executor, rag.ask, question)
    return response

async def ask_stream(question: str, chat_history=None):
    """Non-blocking streaming response that runs RAG in background"""
    rag = get_rag_system()
    loop = asyncio.get_event_loop()
    executor = get_executor()
    
    # Start the RAG processing in a background thread
    future = loop.run_in_executor(executor, rag.ask, question)
    
    # Poll for completion while yielding control
    while not future.done():
        await asyncio.sleep(0.1)  # Small delay to allow other tasks
    
    # Get the result
    try:
        response = await future
        answer = response["answer"]
        
        # Stream the actual answer word by word
        words = answer.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            await asyncio.sleep(0.02)  # Small delay between words
        
        # Send completion signal
        # yield f"data: {{'type': 'complete', 'sources': {len(response.get('source_documents', []))}}}\n\n"
        
    except Exception as e:
        yield f"data: {{'type': 'error', 'content': 'Error: {str(e)}'}}\n\n" 