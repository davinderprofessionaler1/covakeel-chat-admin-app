from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from app.schemas.message import MessageCreate, MessageRead
from app.services import message_service, conversation_service, source_service
from app.services.answer_export import export_docx, export_pdf
from app.schemas.source import SourceRead
from app.core.config import ADMIN_UPLOAD_DIR
from app.core.security import get_current_user
from app.db.mongodb import get_db
from bson import ObjectId

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


async def _owned_assistant_message(msg_id: str, user):
    msg = await message_service.get_message_by_id(msg_id)
    if not msg or msg.sender != "assistant":
        raise HTTPException(status_code=404, detail="Answer not found")
    conv = await conversation_service.get_conversation_by_id(str(msg.conversationId))
    if not conv or str(conv.userId) != str(user._id):
        raise HTTPException(status_code=404, detail="Answer not found")
    return msg


@router.get("/{msg_id}/export/{file_format}")
async def export_answer(msg_id: str, file_format: str, user=Depends(get_current_user)):
    msg = await _owned_assistant_message(msg_id, user)
    if file_format not in {"pdf", "docx"}:
        raise HTTPException(status_code=404, detail="Export format not found")
    sources = await source_service.list_sources_by_message(msg_id)
    maker = export_pdf if file_format == "pdf" else export_docx
    if file_format == "pdf":
        question = await message_service.get_question_for_answer(msg)
        content = maker(msg.text, sources, question=question)
    else:
        content = maker(msg.text, sources)
    media_type = "application/pdf" if file_format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return Response(content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="covakeel-answer.{file_format}"',
        "Cache-Control": "private, no-store",
    })


@router.get("/{msg_id}/sources/{source_id}/pdf")
async def cited_pdf(msg_id: str, source_id: str, download: bool = False, user=Depends(get_current_user)):
    await _owned_assistant_message(msg_id, user)
    sources = await source_service.list_sources_by_message(msg_id)
    source = next((item for item in sources if str(item._id) == source_id), None)
    if not source:
        raise HTTPException(status_code=404, detail="Cited source not found")
    doc_id = (source.metadata or {}).get("document_id")
    if not isinstance(doc_id, str) or not ObjectId.is_valid(doc_id) or str(ObjectId(doc_id)) != doc_id:
        raise HTTPException(status_code=404, detail="Indexed PDF not available")
    document = await get_db().admin_documents.find_one({
        "_id": doc_id, "status": "indexed", "origin": "upload",
    })
    path = ADMIN_UPLOAD_DIR / f"{doc_id}.pdf"
    if not document or not path.is_file():
        raise HTTPException(status_code=404, detail="Indexed PDF not available")
    filename = Path(document["filename"]).name
    disposition = "attachment" if download else "inline"
    content = path.read_bytes()
    return Response(content, media_type="application/pdf", headers={
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(filename, safe='')}",
        "Cache-Control": "private, no-store",
    })
