from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.core.security import get_current_user
from app.services import conversation_service, message_service, source_service, rag_service
from app.schemas.message import MessageCreate, MessageRead
from app.schemas.source import SourceCreate
import time
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])


def require_chat_configuration():
    try:
        rag_service.ensure_rag_configured()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/", response_model=MessageRead)
async def chat(conversationId: str, text: str, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(conversationId)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    require_chat_configuration()

    # Get chat history
    messages = await message_service.list_messages_by_conversation(conversationId)
    chat_history = [(m.sender, m.text) for m in messages]

    # Get RAG answer using async method
    response = await rag_service.ask_async(text, chat_history)

    # Save user message
    user_msg_id = await message_service.create_message(MessageCreate(conversationId=conversationId, sender="user", text=text))

    # Save assistant message
    ai_msg_id = await message_service.create_message(MessageCreate(conversationId=conversationId, sender="assistant", text=response["answer"]))

    # Save sources
    for src in response.get("source_documents", []):
        await source_service.create_source(SourceCreate(messageId=ai_msg_id, filename=src.metadata.get("filename", ""), content=src.page_content, metadata=src.metadata))

    ai_msg = await message_service.get_message_by_id(ai_msg_id)
    return MessageRead(
        id=str(ai_msg._id),
        conversationId=str(ai_msg.conversationId),
        sender=ai_msg.sender,
        text=ai_msg.text,
        createdAt=ai_msg.createdAt
    )


@router.post("/stream")
async def chat_stream(
    conversationId: str,
    text: str,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    conv = await conversation_service.get_conversation_by_id(conversationId)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    require_chat_configuration()

    # Get chat history
    messages = await message_service.list_messages_by_conversation(conversationId)
    chat_history = [(m.sender, m.text) for m in messages]

    # Save user message immediately
    await message_service.create_message(MessageCreate(
        conversationId=conversationId,
        sender="user",
        text=text))

    # Store the response content for later saving
    response_content = []
    sources_info = None

    # Non-blocking streaming generator
    async def streamer():
        nonlocal response_content, sources_info

        try:
            async for chunk in rag_service.ask_stream(text, chat_history):
                response_content.append(chunk)
                yield chunk
        except Exception as e:
            error_chunk = f"'Streaming error: {str(e)}'\n\n"
            response_content.append(error_chunk)
            yield error_chunk

    # Background task to save the complete response
    async def save_to_db():
        try:
            # Extract the actual content from SSE format
            full_content = "".join(response_content)

            if full_content.strip():
                # Save assistant message with the complete response
                await message_service.create_message(MessageCreate(
                    conversationId=conversationId,
                    sender="assistant",
                    text=full_content.strip()
                ))
        except Exception as e:
            print(f"Error saving streamed response to DB: {e}")

    # Add the background task
    background_tasks.add_task(save_to_db)

    # Return streaming response with proper headers for SSE
    return StreamingResponse(
        streamer(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/test-concurrent")
async def test_concurrent():
    """Test endpoint to verify server can handle concurrent requests"""
    request_time = time.time()
    await asyncio.sleep(0.1)  # Small async delay
    return {
        "message": "Server is responsive",
        "timestamp": request_time,
        "server_time": time.time()
    }
