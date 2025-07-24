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
from app.services.whatsapp.whatsapp_service import WhatsAppService

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
    Requires 'messages:send_template' permission.
    """
    db = database.db

    try:
        # Verify conversation exists
        conversation = await db.conversations.find_one(
            {"_id": ObjectId(template_data.conversation_id)}
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )

        # Send template via WhatsApp API
        whatsapp_response = await whatsapp_service.send_template_message(
            to_number=conversation["customer_phone"],
            template_name=template_data.template_name,
            language_code=template_data.language_code,
            parameters=template_data.parameters,
        )

        if not whatsapp_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR,
            )

        # Extract WhatsApp message ID from response
        whatsapp_message_id = None
        if whatsapp_response.get("messages") and len(whatsapp_response["messages"]) > 0:
            whatsapp_message_id = whatsapp_response["messages"][0].get("id")

        # Create message record
        message_dict = {
            "conversation_id": ObjectId(template_data.conversation_id),
            "whatsapp_message_id": whatsapp_message_id,
            "type": "template",
            "direction": "outbound",
            "sender_role": "agent",
            "sender_id": current_user.id,
            "sender_phone": None,
            "sender_name": current_user.name,
            "template_data": {
                "name": template_data.template_name,
                "language": template_data.language_code,
                "parameters": template_data.parameters,
            },
            "status": "sent",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_automated": False,
            "whatsapp_data": whatsapp_response,
        }

        # Insert message
        result = await db.messages.insert_one(message_dict)

        # Update conversation
        await db.conversations.update_one(
            {"_id": ObjectId(template_data.conversation_id)},
            {
                "$set": {
                    "last_message_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {"message_count": 1},
            },
        )

        # Get conversation for audit logging
        conversation = await db.conversations.find_one(
            {"_id": ObjectId(template_data.conversation_id)}
        )

        # Log template sent
        await AuditService.log_message_sent(
            actor_id=str(current_user.id),
            actor_name=f"{current_user.name or current_user.email}",
            conversation_id=template_data.conversation_id,
            customer_phone=conversation.get("customer_phone") if conversation else None,
            department_id=(
                str(conversation.get("department_id"))
                if conversation and conversation.get("department_id")
                else None
            ),
            message_type="template",
            message_id=str(result.inserted_id),
            correlation_id=get_correlation_id(),
        )

        # Fetch created message
        created_message = await db.messages.find_one({"_id": result.inserted_id})

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
