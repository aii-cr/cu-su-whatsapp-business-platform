"""Delete conversation by ID endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.schemas import SuccessResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.services.audit.audit_service import AuditService

router = APIRouter()

@router.delete("/{conversation_id}", response_model=SuccessResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:delete"]))
):
    """
    Delete conversation by ID.
    This will permanently delete the conversation and all associated messages.
    Requires 'conversations:delete' permission.
    """
    db = database.db
    
    try:
        # Validate conversation ID format
        try:
            conversation_obj_id = ObjectId(conversation_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.INVALID_CONVERSATION_ID
            )
        
        # Check if conversation exists
        conversation = await db.conversations.find_one({"_id": conversation_obj_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check access permissions (only assigned agent, super admin, or users with delete_all permission)
        from app.services.auth import check_user_permission
        
        if (conversation.get("assigned_agent_id") != current_user.id and 
            not current_user.is_super_admin and
            not await check_user_permission(current_user.id, "conversations:delete_all")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CONVERSATION_ACCESS_DENIED
            )
        
        # Store conversation data for audit logging
        conversation_data = {
            "customer_phone": conversation.get("customer_phone"),
            "customer_name": conversation.get("customer_name"),
            "status": conversation.get("status"),
            "assigned_agent_id": conversation.get("assigned_agent_id"),
            "department_id": conversation.get("department_id"),
            "message_count": conversation.get("message_count", 0),
            "unread_count": conversation.get("unread_count", 0)
        }
        
        # Delete all messages associated with this conversation
        messages_deleted = await db.messages.delete_many({"conversation_id": conversation_obj_id})
        logger.info(f"Deleted {messages_deleted.deleted_count} messages for conversation {conversation_id}")
        
        # Delete the conversation
        result = await db.conversations.delete_one({"_id": conversation_obj_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Log audit event
        await AuditService.log_event(
            action="conversation_deleted",
            actor_id=str(current_user.id),
            actor_name=f"{current_user.name or current_user.email}",
            conversation_id=conversation_id,
            customer_phone=conversation_data["customer_phone"],
            department_id=str(conversation_data["department_id"]) if conversation_data["department_id"] else None,
            payload={
                "messages_deleted": messages_deleted.deleted_count,
                "conversation_data": conversation_data
            },
            correlation_id=get_correlation_id(),
        )
        
        logger.info(f"Successfully deleted conversation {conversation_id} and {messages_deleted.deleted_count} messages")
        
        return SuccessResponse(
            message=f"Conversation {conversation_id} deleted successfully",
            data={
                "conversation_id": conversation_id,
                "messages_deleted": messages_deleted.deleted_count,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 