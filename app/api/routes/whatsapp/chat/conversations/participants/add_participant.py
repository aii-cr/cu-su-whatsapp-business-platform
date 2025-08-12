"""Add participant endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.conversations.participant import ParticipantIn
from app.services import conversation_service

router = APIRouter()


@router.post("/{conversation_id}/participants", status_code=status.HTTP_204_NO_CONTENT)
async def add_participant(
    conversation_id: str,
    participant: ParticipantIn,
    current_user: User = Depends(require_permissions(["conversation:participants:write"]))
):
    ok = await conversation_service.add_participant(
        conversation_id, str(participant.user_id), participant.role.value, actor_id=str(current_user.id)
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to add participant")
    return None


