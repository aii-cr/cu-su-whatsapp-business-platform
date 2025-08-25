"""Change participant role endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from pydantic import BaseModel, Field
from app.services import conversation_service

router = APIRouter()


class RoleChange(BaseModel):
    role: str = Field(..., pattern="^(primary|agent|observer)$")


@router.patch("/{conversation_id}/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def change_role(
    conversation_id: str,
    participant_id: str,
    body: RoleChange,
    current_user: User = Depends(require_permissions(["conversation:participants:write"]))
):
    ok = await conversation_service.change_participant_role(
        conversation_id, participant_id, body.role, actor_id=str(current_user.id)
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Unable to change role")
    return None


