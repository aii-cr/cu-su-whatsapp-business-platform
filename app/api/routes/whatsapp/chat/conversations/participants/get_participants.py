"""Get participants endpoint."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service

router = APIRouter()


@router.get("/{conversation_id}/participants")
async def get_participants(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversation:participants:read"]))
) -> Dict[str, Any]:
    items = await conversation_service.get_participants(conversation_id)
    return {"items": items, "conversation_id": conversation_id}


