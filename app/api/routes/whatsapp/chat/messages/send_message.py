"""Send text message endpoint."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_in import MessageSend
from app.schemas.whatsapp.chat.message_out import MessageResponse, MessageSendResponse
from app.services import audit_service
from app.services.auth import require_permissions, check_user_permission
from app.services import whatsapp_service
from app.services import message_service, conversation_service
from app.core.error_handling import handle_database_error

router = APIRouter()

# WhatsApp service is imported from app.services


@router.post("/send", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageSend, current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Send a text message to a customer.

    - You may provide either a `conversation_id` (to send in an existing conversation) or a `customer_phone` (to auto-create or reuse a conversation for that customer).
    - If only `customer_phone` is provided, the backend will look up an active/pending conversation for that phone, or create a new one if none exists.
    - The response will always include the used/created `conversation_id`.

    Request payload examples:
    - {"conversation_id": "<existing_conversation_id>", "text_content": "Hello!"}
    - {"customer_phone": "+1234567890", "text_content": "Hello!"}

    Returns the sent message and WhatsApp API response.
    Requires 'messages:send' permission.
    """
    # ===== REQUEST VALIDATION =====
    logger.info("🔵 [SEND_MESSAGE] Starting message send process")
    logger.info(
        f"📝 [SEND_MESSAGE] Payload: conversation_id={message_data.conversation_id}, phone={message_data.customer_phone}, text_length={len(message_data.text_content)}"
    )
    logger.info(
        f"👤 [SEND_MESSAGE] User: {current_user.email} (ID: {current_user.id}, Super Admin: {current_user.is_super_admin})"
    )

    try:
        conversation = None
        conversation_id = message_data.conversation_id

        # ===== CONVERSATION LOOKUP/CREATION =====
        if not conversation_id and message_data.customer_phone:
            logger.info(
                f"🔍 [SEND_MESSAGE] Looking up conversation for phone: {message_data.customer_phone}"
            )

            # Use conversation service to find or create conversation
            conversation = await conversation_service.find_conversation_by_phone(message_data.customer_phone)
            
            if conversation:
                conversation_id = str(conversation["_id"])
                logger.info(f"✅ [SEND_MESSAGE] Found existing conversation: {conversation_id}")
            else:
                logger.info(
                    f"🆕 [SEND_MESSAGE] Creating new conversation for phone: {message_data.customer_phone}"
                )

                # Create new conversation using service
                conversation = await conversation_service.create_conversation(
                    customer_phone=message_data.customer_phone,
                    created_by=current_user.id
                )
                conversation_id = str(conversation["_id"])
                logger.info(f"✅ [SEND_MESSAGE] Successfully created conversation: {conversation_id}")

        if not conversation:
            if not conversation_id:
                logger.error("❌ [SEND_MESSAGE] No conversation_id or customer_phone provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either conversation_id or customer_phone must be provided.",
                )

            # Get conversation using service
            conversation = await conversation_service.get_conversation(conversation_id)

            if not conversation:
                logger.error(f"❌ [SEND_MESSAGE] Conversation not found: {conversation_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
                )

        logger.info(
            f"📋 [SEND_MESSAGE] Using conversation: {conversation_id} (Status: {conversation.get('status')}, Phone: {conversation.get('customer_phone')})"
        )

        # ===== PERMISSION CHECK =====
        if not current_user.is_super_admin:
            # Check if user has permission to send messages to this conversation
            if conversation.get("assigned_agent_id") != current_user.id and not await check_user_permission(current_user.id, "messages:send_all"):
                logger.warning(f"❌ [SEND_MESSAGE] Permission denied for user {current_user.id} on conversation {conversation_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorCode.PERMISSION_DENIED
                )

        # ===== SEND MESSAGE VIA WHATSAPP =====
        logger.info(f"📤 [SEND_MESSAGE] Sending message via WhatsApp API")
        
        whatsapp_response = await whatsapp_service.send_text_message(
            to_number=conversation["customer_phone"],
            text=message_data.text_content
        )
        
        if not whatsapp_response:
            logger.error("❌ [SEND_MESSAGE] Failed to send message via WhatsApp API")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to send message via WhatsApp API"
            )

        # ===== SAVE MESSAGE TO DATABASE =====
        logger.info(f"💾 [SEND_MESSAGE] Saving message to database")
        
        # Create message using service
        message = await message_service.create_message(
            conversation_id=conversation_id,
            message_type="text",
            direction="outbound",
            sender_role="agent",
            sender_id=current_user.id,
            sender_name=current_user.name,
            text_content=message_data.text_content,
            whatsapp_message_id=whatsapp_response.get("messages", [{}])[0].get("id"),
            whatsapp_data=whatsapp_response,
            status="sent"
        )
        
        # Update conversation message count
        await conversation_service.increment_message_count(conversation_id)

        # ===== UPDATE CONVERSATION STATUS =====
        logger.info(f"🔄 [SEND_MESSAGE] Updating conversation status")
        
        # Update conversation status based on current state
        status_update = {}
        current_status = conversation.get("status", "pending")
        
        if current_status == "pending":
            # First agent response - activate conversation
            status_update["status"] = "active"
            status_update["assigned_agent_id"] = current_user.id
            logger.info(f"✅ [SEND_MESSAGE] Activating conversation {conversation_id}")
        elif current_status == "waiting":
            # Agent responding to customer - set back to active
            status_update["status"] = "active"
            logger.info(f"✅ [SEND_MESSAGE] Reactivating conversation {conversation_id}")
        
        # Update conversation if status needs to change
        if status_update:
            await conversation_service.update_conversation(
                conversation_id=conversation_id,
                update_data=status_update,
                updated_by=current_user.id
            )

        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.log_message_sent(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            customer_phone=conversation["customer_phone"],
            department_id=str(conversation.get("department_id")) if conversation.get("department_id") else None,
            message_type="text",
            message_id=str(message["_id"]),
            correlation_id=correlation_id
        )

        # ===== RESPONSE =====
        logger.info(f"✅ [SEND_MESSAGE] Message sent successfully. Message ID: {message['_id']}")
        
        return MessageSendResponse(
            message=MessageResponse(**message),
            whatsapp_response=whatsapp_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [SEND_MESSAGE] Unexpected error: {str(e)}")
        raise handle_database_error(e, "send_message", "message")
