from fastapi import APIRouter, HTTPException
from app.services.database_service import ChatPlatformService

router = APIRouter()

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    try:
        messages = await ChatPlatformService.get_messages_by_conversation(conversation_id)
        return {"conversation_id": conversation_id, "messages": messages}
    except HTTPException as e:
        raise e 