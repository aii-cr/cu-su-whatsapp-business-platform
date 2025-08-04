"""Send media message endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from bson import ObjectId

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.whatsapp.chat.message_in import MediaMessageSend
from app.schemas.whatsapp.chat.message_out import MessageSendResponse, MessageResponse
from app.services import whatsapp_service

router = APIRouter()

# WhatsApp service is imported from app.services

@router.post("/media", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_media_message(
    media_data: MediaMessageSend,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Send a media message (image, audio, video, document) to a customer.
    Requires 'messages:send' permission.
    """
    db = database.db
    
    try:
        # Verify conversation exists
        conversation = await db.conversations.find_one({
            "_id": ObjectId(media_data.conversation_id)
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Send media via WhatsApp API
        whatsapp_response = await whatsapp_service.send_media_message(
            to_number=conversation["customer_phone"],
            media_type=media_data.media_type,
            media_url=media_data.media_url,
            caption=media_data.caption
        )
        
        if not whatsapp_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR
            )
        
        # Create message record
        message_dict = {
            "conversation_id": ObjectId(media_data.conversation_id),
            "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
            "type": media_data.media_type,
            "direction": "outbound",
            "sender_role": "agent",
            "sender_id": current_user.id,
            "sender_phone": None,
            "sender_name": current_user.name,
            "media_url": media_data.media_url,
            "media_metadata": {
                "caption": media_data.caption,
                "filename": media_data.filename
            },
            "status": "sent",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "is_automated": False,
            "whatsapp_data": {
                "phone_number_id": whatsapp_response.get("messages", [{}])[0].get("phone_number_id"),
                "business_account_id": whatsapp_response.get("messages", [{}])[0].get("business_account_id")
            }
        }
        
        # Insert message
        result = await db.messages.insert_one(message_dict)
        
        # Update conversation
        await db.conversations.update_one(
            {"_id": ObjectId(media_data.conversation_id)},
            {
                "$set": {
                    "last_message_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                "$inc": {
                    "message_count": 1
                }
            }
        )
        
        # Fetch created message
        created_message = await db.messages.find_one({"_id": result.inserted_id})
        
        return MessageSendResponse(
            message=MessageResponse(**created_message),
            whatsapp_response=whatsapp_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send media message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 