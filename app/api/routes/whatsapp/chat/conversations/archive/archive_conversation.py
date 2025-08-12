"""Archive conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service

router = APIRouter()


@router.post("/{conversation_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
async def archive_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversation:archive"]))
):
    ok = await conversation_service.archive_conversation(conversation_id, actor_id=str(current_user.id))
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to archive conversation")
    return None


