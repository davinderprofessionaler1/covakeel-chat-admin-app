from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.conversation import ConversationCreate, ConversationRead, ConversationUpdate
from app.services import conversation_service
from app.core.security import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(conv: ConversationCreate, user=Depends(get_current_user)):
    conv_id = await conversation_service.create_conversation(str(user._id), conv)
    created = await conversation_service.get_conversation_by_id(conv_id)
    return ConversationRead(
        id=str(created._id),
        userId=str(created.userId),
        title=created.title,
        createdAt=created.createdAt.replace(tzinfo=timezone.utc).isoformat(),
        updatedAt=created.updatedAt.replace(tzinfo=timezone.utc).isoformat()
    )

@router.get("/", response_model=list[ConversationRead])
async def list_conversations(user=Depends(get_current_user)):
    conversations = await conversation_service.list_conversations_by_user(str(user._id))
    return [ConversationRead(
        id=str(c._id),
        userId=str(c.userId),
        title=c.title,
        createdAt=c.createdAt.replace(tzinfo=timezone.utc).isoformat(),
        updatedAt=c.updatedAt.replace(tzinfo=timezone.utc).isoformat()
    ) for c in conversations]

@router.get("/{conv_id}", response_model=ConversationRead)
async def get_conversation(conv_id: str, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(conv_id)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationRead(
        id=str(conv._id),
        userId=str(conv.userId),
        title=conv.title,
        createdAt=conv.createdAt.replace(tzinfo=timezone.utc).isoformat(),
        updatedAt=conv.updatedAt.replace(tzinfo=timezone.utc).isoformat()
    )

@router.put("/{conv_id}", response_model=ConversationRead)
async def update_conversation(conv_id: str, conv_update: ConversationUpdate, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(conv_id)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    updated = await conversation_service.update_conversation(conv_id, conv_update)
    return ConversationRead(
        id=str(updated._id),
        userId=str(updated.userId),
        title=updated.title,
        createdAt=updated.createdAt.replace(tzinfo=timezone.utc).isoformat(),
        updatedAt=updated.updatedAt.replace(tzinfo=timezone.utc).isoformat()
    )

@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conv_id: str, user=Depends(get_current_user)):
    conv = await conversation_service.get_conversation_by_id(conv_id)
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    await conversation_service.delete_conversation(conv_id)
    return None 