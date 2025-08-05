"""Get conversation endpoint - Optimized with caching."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationResponse
from app.services import conversation_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    response: Response,
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get a specific conversation by ID with optimized caching.
    
    Note: For better performance, consider using the combined endpoint
    /conversations/{id}/with-messages which loads conversation + messages
    in a single optimized call.
    
    Args:
        conversation_id: ID of the conversation
        response: FastAPI response object for setting headers
        current_user: Current authenticated user
        
    Returns:
        Conversation details with caching headers
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🔍 [GET_CONVERSATION] Loading conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Get conversation using service
        conversation = await conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            logger.warning(
                f"❌ [GET_CONVERSATION] Conversation {conversation_id} not found",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": str(current_user.id),
                    "correlation_id": correlation_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_response(ErrorCode.CONVERSATION_NOT_FOUND)
            )
        
        # Check access permissions (basic check)
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                conversation.get("created_by") != current_user.id):
                logger.warning(
                    f"🚫 [GET_CONVERSATION] Access denied to conversation {conversation_id}",
                    extra={
                        "conversation_id": conversation_id,
                        "user_id": str(current_user.id),
                        "correlation_id": correlation_id
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_error_response(ErrorCode.CONVERSATION_ACCESS_DENIED)
                )
        
        # ===== AUDIT LOGGING =====
        await audit_service.log_conversation_accessed(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            customer_phone=conversation.get("customer_phone"),
            correlation_id=correlation_id
        )
        
        # Set caching headers for better performance
        # Cache for 30 seconds for conversation metadata
        response.headers["Cache-Control"] = "private, max-age=30"
        response.headers["ETag"] = f'"{conversation_id}-{conversation.get("updated_at", "")}"'
        
        logger.info(
            f"✅ [GET_CONVERSATION] Successfully retrieved conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        return ConversationResponse(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 [GET_CONVERSATION] Error retrieving conversation {conversation_id}: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise handle_database_error(e, "get_conversation", "conversation") 