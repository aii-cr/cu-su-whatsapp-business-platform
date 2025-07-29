"""Send template message endpoint."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.client import database
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_in import TemplateMessageSend
from app.schemas.whatsapp.chat.message_out import MessageResponse, MessageSendResponse
from app.services.audit.audit_service import AuditService
from app.services.auth import require_permissions
from app.services.whatsapp.whatsapp_service import WhatsAppService, WhatsAppAPIError
from app.services.whatsapp.conversation.conversation_service import conversation_service
from app.services.whatsapp.message.message_service import message_service
from app.services.websocket.websocket_service import websocket_service

router = APIRouter()

# Initialize WhatsApp service
whatsapp_service = WhatsAppService()


@router.post("/template", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_template_message(
    template_data: TemplateMessageSend,
    current_user: User = Depends(require_permissions(["messages:send_template"])),
):
    """
    Send a template message to a customer.
    Accepts either conversation_id (existing conversation) or customer_phone (new conversation).
    Requires 'messages:send_template' permission.
    """
    db = database.db

    try:
        conversation = None
        conversation_id = None
        customer_phone = None

        # Determine if we're using conversation_id or customer_phone
        if template_data.conversation_id:
            # Use existing conversation
            conversation = await db.conversations.find_one(
                {"_id": ObjectId(template_data.conversation_id)}
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
                )
            
            conversation_id = template_data.conversation_id
            customer_phone = conversation["customer_phone"]
            
        elif template_data.customer_phone:
            # Create new conversation for new customer
            customer_phone = template_data.customer_phone
            
            # Check if conversation already exists for this phone
            existing_conversation = await db.conversations.find_one(
                {"customer_phone": customer_phone}
            )
            
            if existing_conversation:
                conversation = existing_conversation
                conversation_id = str(existing_conversation["_id"])
                logger.info(f"Found existing conversation {conversation_id} for phone {customer_phone}")
            else:
                # Create new conversation
                new_conversation = await conversation_service.create_conversation(
                    customer_phone=customer_phone,
                    customer_name=None,  # Will be updated when customer responds
                    department_id=None,  # Default department or assign based on rules
                    assigned_agent_id=current_user.id,
                    created_by=current_user.id
                )
                
                conversation = new_conversation
                conversation_id = str(new_conversation["_id"])
                logger.info(f"Created new conversation {conversation_id} for phone {customer_phone}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either conversation_id or customer_phone must be provided"
            )

        # Send template via WhatsApp API
        try:
            whatsapp_response = await whatsapp_service.send_template_message(
                to_number=customer_phone,
                template_name=template_data.template_name,
                language_code=template_data.language_code,
                parameters=template_data.parameters,
            )
            logger.info(f"WhatsApp response: {whatsapp_response}")
        except WhatsAppAPIError as e:
            logger.error(f"WhatsApp API error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR,
            )
        except Exception as e:
            logger.error(f"Unexpected error sending template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.INTERNAL_SERVER_ERROR,
            )

        if not whatsapp_response:
            logger.error(f"WhatsApp response is None or empty: {whatsapp_response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR,
            )

        logger.info(f"WhatsApp response type: {type(whatsapp_response)}")
        logger.info(f"WhatsApp response keys: {whatsapp_response.keys() if isinstance(whatsapp_response, dict) else 'Not a dict'}")

        # Extract WhatsApp message ID from response
        whatsapp_message_id = None
        if whatsapp_response.get("messages") and len(whatsapp_response["messages"]) > 0:
            whatsapp_message_id = whatsapp_response["messages"][0].get("id")

        logger.info(f"WhatsApp message ID: {whatsapp_message_id}")

        # Create message record using service
        logger.info("About to create message...")
        try:
            message_dict = await message_service.create_message(
                conversation_id=conversation_id,
                message_type="template",
                direction="outbound",
                sender_role="agent",
                sender_id=current_user.id,
                sender_phone=None,
                sender_name=current_user.name,
                template_data={
                    "name": template_data.template_name,
                    "language": template_data.language_code,
                    "parameters": template_data.parameters,
                },
                whatsapp_message_id=whatsapp_message_id,
                is_automated=False,
                whatsapp_data={
                    **(whatsapp_response or {}),
                    "display_phone_number": "15551732531",  # From settings
                },
                status="sent"
            )
            logger.info("Message created successfully")
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise

        logger.info(f"Message dict created: {message_dict}")
        logger.info(f"Message dict type: {type(message_dict)}")
        logger.info(f"Message dict keys: {message_dict.keys() if isinstance(message_dict, dict) else 'Not a dict'}")

        # Update conversation message count
        logger.info("About to increment message count...")
        try:
            await conversation_service.increment_message_count(conversation_id)
            logger.info("Message count incremented successfully")
        except Exception as e:
            logger.error(f"Error incrementing message count: {str(e)}")
            raise

        # Conversation already updated by service

        # Log template sent
        await AuditService.log_message_sent(
            actor_id=str(current_user.id),
            actor_name=f"{current_user.name or current_user.email}",
            conversation_id=conversation_id,
            customer_phone=customer_phone,
            department_id=(
                str(conversation.get("department_id"))
                if conversation and conversation.get("department_id")
                else None
            ),
            message_type="template",
            message_id=str(message_dict["_id"]),
            correlation_id=get_correlation_id(),
        )

        # ===== WEBSOCKET NOTIFICATION =====
        try:
           

            await websocket_service.notify_new_message(conversation_id, message_dict)
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {str(e)}")

        # ===== RESPONSE =====
        created_message = message_dict

        return MessageSendResponse(
            message=MessageResponse(**created_message), whatsapp_response=whatsapp_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send template message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR,
        )
