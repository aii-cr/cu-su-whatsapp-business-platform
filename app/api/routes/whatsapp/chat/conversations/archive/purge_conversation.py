"""Purge conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service

router = APIRouter()


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def purge_conversation(
    conversation_id: str,
    confirm: bool = Query(False, description="Must be true to purge"),
    current_user: User = Depends(require_permissions(["conversation:purge"]))
):
    ok = await conversation_service.purge_conversation(conversation_id, confirm=confirm, actor_id=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to purge conversation or confirmation missing")
    return None


