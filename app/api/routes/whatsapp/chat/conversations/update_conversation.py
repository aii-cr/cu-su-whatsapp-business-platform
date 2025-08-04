from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.client import database
from app.db.models.auth import User
from app.schemas.whatsapp.chat import ConversationResponse, ConversationUpdate
from app.services import audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(require_permissions(["conversations:update"])),
):
    """
    Update conversation by ID.
    Requires 'conversations:update' permission.
    """
    db = database.db

    try:
        conversation_obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorCode.INVALID_CONVERSATION_ID
        )

    # Prepare update data
    update_data = conversation_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.id

        result = await db.conversations.update_one(
            {"_id": conversation_obj_id}, {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )

        # Get conversation for audit logging
        conversation = await db.conversations.find_one({"_id": conversation_obj_id})

        # Log appropriate audit events based on what was updated
        if "priority" in update_data:
            await audit_service.log_priority_changed(
                actor_id=str(current_user.id),
                actor_name=f"{current_user.name or current_user.email}",
                conversation_id=conversation_id,
                customer_phone=conversation.get("customer_phone"),
                department_id=(
                    str(conversation.get("department_id"))
                    if conversation.get("department_id")
                    else None
                ),
                from_priority=conversation.get("priority"),
                to_priority=update_data.get("priority"),
                correlation_id=get_correlation_id(),
            )

        if "department_id" in update_data:
            await audit_service.log_agent_transfer(
                actor_id=str(current_user.id),
                actor_name=f"{current_user.name or current_user.email}",
                conversation_id=conversation_id,
                customer_phone=conversation.get("customer_phone"),
                from_department_id=(
                    str(conversation.get("department_id"))
                    if conversation.get("department_id")
                    else None
                ),
                to_department_id=(
                    str(update_data.get("department_id"))
                    if update_data.get("department_id")
                    else None
                ),
                reason="Department update via API",
                correlation_id=get_correlation_id(),
            )

        # For other general updates, use the general audit log
        if any(key not in ["priority", "department_id"] for key in update_data.keys()):
            await audit_service.log_event(
                action="conversation_updated",
                actor_id=str(current_user.id),
                actor_name=f"{current_user.name or current_user.email}",
                conversation_id=conversation_id,
                customer_phone=conversation.get("customer_phone"),
                department_id=(
                    str(conversation.get("department_id"))
                    if conversation.get("department_id")
                    else None
                ),
                payload={"updated_fields": list(update_data.keys())},
                correlation_id=get_correlation_id(),
            )

    # Return updated conversation
    updated_conversation = await db.conversations.find_one({"_id": conversation_obj_id})
    return ConversationResponse(**updated_conversation)
