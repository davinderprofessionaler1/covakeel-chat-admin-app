from fastapi import FastAPI
from app.routes.user_routes import user_routes
from app.routes.auth_routes import auth_routes
from app.routes.conversation_routes import conversation_routes
from app.routes.message_routes import message_routes
from app.routes.chat_routes import chat_routes
from fastapi.middleware.cors import CORSMiddleware
import asyncio

origins = [
    "http://localhost:8080",
]

app = FastAPI(
    title="Indian Law Acts RAG Chatbot API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(user_routes)
app.include_router(auth_routes)
app.include_router(conversation_routes)
app.include_router(message_routes)
app.include_router(chat_routes)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],    # Allow all headers
)

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    # Pre-warm the RAG system in background
    from app.services.rag_service import get_rag_system
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, get_rag_system)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    from app.services.rag_service import get_executor
    executor = get_executor()
    if executor:
        executor.shutdown(wait=True) 