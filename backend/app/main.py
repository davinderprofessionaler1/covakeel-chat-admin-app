import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from bson.errors import InvalidId
from fastapi.responses import JSONResponse

from app.core.config import CORS_ORIGINS
from app.db.mongodb import get_db, mongodb
from app.services.rag_service import get_rag_status, shutdown_executor
from app.routes.user_routes import user_routes
from app.routes.auth_routes import auth_routes
from app.routes.conversation_routes import conversation_routes
from app.routes.message_routes import message_routes
from app.routes.chat_routes import chat_routes
from app.controllers.admin_controller import router as admin_routes
from app.services.admin_service import seed_documents, recover_interrupted_uploads


@asynccontextmanager
async def lifespan(app):
    db = get_db()
    await db.command("ping")
    await db.users.create_index("username", unique=True)
    await db.conversations.create_index([("userId", 1), ("updatedAt", -1)])
    await db.messages.create_index([("conversationId", 1), ("createdAt", 1)])
    await seed_documents()
    await recover_interrupted_uploads()
    try:
        yield
    finally:
        await asyncio.to_thread(shutdown_executor)
        if mongodb.client is not None:
            mongodb.client.close()
            mongodb.client = None


app = FastAPI(title="Indian Law Acts RAG Chatbot API", lifespan=lifespan)
for router in [user_routes, auth_routes, conversation_routes, message_routes, chat_routes, admin_routes]:
    app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidId)
async def invalid_id_handler(request: Request, exc: InvalidId):
    return JSONResponse(status_code=400, content={"detail": "Invalid identifier"})


@app.get("/")
async def health_check():
    try:
        await get_db().command("ping")
    except Exception:
        raise HTTPException(status_code=503, detail="MongoDB is unavailable")
    return {"status": "ok", "database": "connected", "rag": get_rag_status()}
