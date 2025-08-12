"""Restore conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service

router = APIRouter()


@router.post("/{conversation_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversation:restore"]))
):
    ok = await conversation_service.restore_conversation(conversation_id, actor_id=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to restore conversation")
    return None


