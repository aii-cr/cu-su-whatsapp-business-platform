"""Send text message endpoint."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.client import database
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_in import MessageSend
from app.schemas.whatsapp.chat.message_out import MessageResponse, MessageSendResponse
from app.services.audit.audit_service import AuditService
from app.services.auth import require_permissions
from app.services.whatsapp.whatsapp_service import WhatsAppService
from app.services.whatsapp.message.message_service import message_service
from app.services.whatsapp.conversation.conversation_service import conversation_service

router = APIRouter()

# Initialize WhatsApp service
whatsapp_service = WhatsAppService()


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
    db = database.db

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

            conversation = await db.conversations.find_one(
                {
                    "customer_phone": message_data.customer_phone,
                    "status": {"$in": ["active", "pending"]},
                }
            )

            if conversation:
                conversation_id = str(conversation["_id"])
                logger.info(f"✅ [SEND_MESSAGE] Found existing conversation: {conversation_id}")
            else:
                logger.info(
                    f"🆕 [SEND_MESSAGE] Creating new conversation for phone: {message_data.customer_phone}"
                )

                conversation_dict = {
                    "customer_phone": message_data.customer_phone,
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "message_count": 0,
                    "unread_count": 0,
                    "created_by": current_user.id,
                    "channel": "whatsapp",
                    "priority": "normal",
                    "customer_type": "b2c",
                    "tags": [],
                    "metadata": {},
                }

                try:
                    result = await db.conversations.insert_one(conversation_dict)
                    conversation_id = str(result.inserted_id)
                    conversation = await db.conversations.find_one({"_id": result.inserted_id})
                    logger.info(
                        f"✅ [SEND_MESSAGE] Successfully created conversation: {conversation_id}"
                    )
                except Exception as db_error:
                    logger.error(
                        f"❌ [SEND_MESSAGE] Failed to create conversation: {str(db_error)}"
                    )
                    if "duplicate key error" in str(db_error).lower():
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="A conversation already exists for this customer",
                        )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create conversation",
                    )

        if not conversation:
            if not conversation_id:
                logger.error("❌ [SEND_MESSAGE] No conversation_id or customer_phone provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either conversation_id or customer_phone must be provided.",
                )

            conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})

            if not conversation:
                logger.error(f"❌ [SEND_MESSAGE] Conversation not found: {conversation_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
                )

        logger.info(
            f"📋 [SEND_MESSAGE] Using conversation: {conversation_id} (Status: {conversation.get('status')}, Phone: {conversation.get('customer_phone')})"
        )

        # ===== PERMISSION CHECK =====
        from app.services.auth import check_user_permission

        if (
            conversation.get("assigned_agent_id") != current_user.id
            and conversation.get("created_by") != current_user.id
            and not current_user.is_super_admin
            and not await check_user_permission(current_user.id, "messages:send_all")
        ):
            logger.warning(f"🚫 [SEND_MESSAGE] Access denied for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=ErrorCode.CONVERSATION_ACCESS_DENIED
            )

        logger.info(f"✅ [SEND_MESSAGE] Permission check passed")

        # ===== WHATSAPP API CALL =====
        logger.info(
            f"📤 [SEND_MESSAGE] Sending WhatsApp message to {conversation['customer_phone']}"
        )

        whatsapp_response = await whatsapp_service.send_text_message(
            to_number=conversation["customer_phone"],
            text=message_data.text_content,
            reply_to_message_id=message_data.reply_to_message_id,
        )

        if not whatsapp_response:
            logger.error(
                f"❌ [SEND_MESSAGE] WhatsApp API failed for conversation {conversation_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR,
            )

        logger.info(
            f"✅ [SEND_MESSAGE] WhatsApp API success: {whatsapp_response.get('messages', [{}])[0].get('id', 'unknown')}"
        )

        # ===== MESSAGE CREATION =====
        # Create message using service
        message_dict = await message_service.create_message(
            conversation_id=conversation_id,
            message_type="text",
            direction="outbound",
            sender_role="agent",
            sender_id=current_user.id,
            sender_phone=None,  # Business phone
            sender_name=current_user.name,
            text_content=message_data.text_content,
            whatsapp_message_id=whatsapp_response.get("messages", [{}])[0].get("id"),
            reply_to_message_id=message_data.reply_to_message_id,
            is_automated=False,
            whatsapp_data={
                "phone_number_id": whatsapp_response.get("messages", [{}])[0].get("phone_number_id"),
                "business_account_id": whatsapp_response.get("messages", [{}])[0].get("business_account_id"),
                "display_phone_number": "15551732531",  # From settings
            },
            status="sent"
        )
        
        logger.info(f"✅ [SEND_MESSAGE] Message saved to database: {message_dict['_id']}")

        # ===== CONVERSATION UPDATE =====
        await conversation_service.increment_message_count(conversation_id)
        logger.info(f"✅ [SEND_MESSAGE] Conversation {conversation_id} updated")

        # ===== AUDIT LOG =====
        await AuditService.log_message_sent(
            actor_id=str(current_user.id),
            actor_name=f"{current_user.name or current_user.email}",
            conversation_id=conversation_id,
            customer_phone=conversation["customer_phone"],
            department_id=(
                str(conversation.get("department_id"))
                if conversation.get("department_id")
                else None
            ),
            message_type="text",
            message_id=str(result.inserted_id),
            correlation_id=get_correlation_id(),
        )

        # ===== WEBSOCKET NOTIFICATION =====
        try:
            from app.services.websocket.websocket_service import websocket_service

            created_message = await db.messages.find_one({"_id": result.inserted_id})
            await websocket_service.notify_new_message(conversation_id, created_message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {str(e)}")

        # ===== RESPONSE =====
        created_message = await db.messages.find_one({"_id": result.inserted_id})
        logger.info(f"🎉 [SEND_MESSAGE] Successfully completed for conversation {conversation_id}")

        return MessageSendResponse(
            message=MessageResponse(**created_message), whatsapp_response=whatsapp_response
        )

    except HTTPException as he:
        logger.error(f"❌ [SEND_MESSAGE] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ [SEND_MESSAGE] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR,
        )
