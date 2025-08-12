"""Remove participant endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service

router = APIRouter()


@router.delete("/{conversation_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    conversation_id: str,
    participant_id: str,
    current_user: User = Depends(require_permissions(["conversation:participants:write"]))
):
    ok = await conversation_service.remove_participant(conversation_id, participant_id, actor_id=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to remove participant")
    return None


