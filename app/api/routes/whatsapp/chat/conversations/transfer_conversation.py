from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.client import database
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationTransfer, ConversationResponse
from app.services import audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.post("/{conversation_id}/transfer", response_model=ConversationResponse)
async def transfer_conversation(
    conversation_id: str,
    transfer_data: ConversationTransfer,
    current_user: User = Depends(require_permissions(["conversations:transfer"])),
):
    """
    Transfer a conversation to another agent or department.
    Requires 'conversations:transfer' permission.
    """
    try:
        conversation_obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorCode.INVALID_CONVERSATION_ID
        )

    try:
        db = database.db
        
        # Get current conversation
        conversation = await db.conversations.find_one({"_id": conversation_obj_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check if conversation is already closed
        if conversation.get("status") == "resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Cannot transfer a closed conversation"
            )
        
        # Validate transfer target
        if not transfer_data.to_agent_id and not transfer_data.to_department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either to_agent_id or to_department_id must be provided"
            )
        
        # If transferring to agent, validate agent exists
        if transfer_data.to_agent_id:
            try:
                target_agent_id = ObjectId(transfer_data.to_agent_id)
                target_agent = await db.users.find_one({"_id": target_agent_id})
                if not target_agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Target agent not found"
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid target agent ID"
                )
        
        # If transferring to department, validate department exists
        if transfer_data.to_department_id:
            try:
                target_department_id = ObjectId(transfer_data.to_department_id)
                target_department = await db.departments.find_one({"_id": target_department_id})
                if not target_department:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Target department not found"
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid target department ID"
                )
        
        # Store current assignment for audit
        current_agent_id = conversation.get("assigned_agent_id")
        current_department_id = conversation.get("department_id")
        
        # Prepare update data
        update_data = {
            "status": "pending",  # Reset to pending for new assignment
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        # Update assignment
        if transfer_data.to_agent_id:
            update_data["assigned_agent_id"] = ObjectId(transfer_data.to_agent_id)
            # Clear department assignment when transferring to specific agent
            update_data["department_id"] = None
        else:
            # Transfer to department - clear agent assignment
            update_data["assigned_agent_id"] = None
            update_data["department_id"] = ObjectId(transfer_data.to_department_id)
        
        # Add to previous agents list if transferring to different agent
        if transfer_data.to_agent_id and current_agent_id:
            previous_agents = conversation.get("previous_agents", [])
            if current_agent_id not in previous_agents:
                previous_agents.append(current_agent_id)
                update_data["previous_agents"] = previous_agents
        
        # Update conversation
        result = await db.conversations.update_one(
            {"_id": conversation_obj_id}, {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Get updated conversation for response
        updated_conversation = await db.conversations.find_one({"_id": conversation_obj_id})
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.log_agent_transfer(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            customer_phone=conversation.get("customer_phone"),
            from_department_id=str(current_department_id) if current_department_id else None,
            to_department_id=str(update_data.get("department_id")) if update_data.get("department_id") else None,
            from_agent_id=str(current_agent_id) if current_agent_id else None,
            to_agent_id=str(update_data.get("assigned_agent_id")) if update_data.get("assigned_agent_id") else None,
            reason=transfer_data.reason,
            correlation_id=correlation_id
        )
        
        logger.info(f"Conversation {conversation_id} transferred by user {current_user.id}")
        
        return ConversationResponse(**updated_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error transferring conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transfer conversation"
        ) 