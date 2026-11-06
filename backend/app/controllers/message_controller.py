from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.message import MessageCreate, MessageRead
from app.services import message_service, conversation_service, source_service
from app.schemas.source import SourceRead
from app.core.security import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(msg: MessageCreate, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(msg.conversationId)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg_id = await message_service.create_message(msg)
    created = await message_service.get_message_by_id(msg_id)
    return MessageRead(
        id=str(created._id),
        conversationId=str(created.conversationId),
        sender=created.sender,
        text=created.text,
        createdAt=created.createdAt
    )

@router.get("/by_conversation/{conv_id}", response_model=list[MessageRead])
async def list_messages(conv_id: str, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(conv_id)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await message_service.list_messages_by_conversation(conv_id)
    return [MessageRead(
        id=str(m._id),
        conversationId=str(m.conversationId),
        sender=m.sender,
        text=m.text,
        createdAt=m.createdAt
    ) for m in messages]

@router.get("/{msg_id}", response_model=MessageRead)
async def get_message(msg_id: str, user=Depends(get_current_user)):
    msg = await message_service.get_message_by_id(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    conv = await conversation_service.get_conversation_by_id(str(msg.conversationId))
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return MessageRead(
        id=str(msg._id),
        conversationId=str(msg.conversationId),
        sender=msg.sender,
        text=msg.text,
        createdAt=msg.createdAt
    )

@router.delete("/{msg_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(msg_id: str, user=Depends(get_current_user)):
    msg = await message_service.get_message_by_id(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    conv = await conversation_service.get_conversation_by_id(str(msg.conversationId))
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    await message_service.delete_message(msg_id)
    return None

@router.get("/{msg_id}/sources", response_model=list[SourceRead])
async def get_message_sources(msg_id: str, user=Depends(get_current_user)):
    msg = await message_service.get_message_by_id(msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    conv = await conversation_service.get_conversation_by_id(str(msg.conversationId))
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    sources = await source_service.list_sources_by_message(msg_id)
    return [SourceRead(id=str(s._id), messageId=str(s.messageId), filename=s.filename,
                       content=s.content, metadata=s.metadata, createdAt=s.createdAt)
            for s in sources]
