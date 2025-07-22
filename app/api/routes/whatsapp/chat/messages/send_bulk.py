"""Send bulk messages endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.whatsapp.chat.message_in import BulkMessageSend
from app.schemas.whatsapp.chat.message_out import MessageSendResponse
from app.services.whatsapp.whatsapp_service import WhatsAppService

router = APIRouter()

# Initialize WhatsApp service
whatsapp_service = WhatsAppService()

@router.post("/bulk-send", response_model=List[MessageSendResponse])
async def send_bulk_messages(
    bulk_data: BulkMessageSend,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permissions(["messages:send_bulk"]))
):
    """
    Send messages to multiple conversations in bulk.
    Requires 'messages:send_bulk' permission.
    """
    db = database.db
    
    try:
        results = []
        
        for message_data in bulk_data.messages:
            try:
                # Verify conversation exists
                conversation = await db.conversations.find_one({
                    "_id": ObjectId(message_data.conversation_id)
                })
                
                if not conversation:
                    results.append({
                        "conversation_id": message_data.conversation_id,
                        "success": False,
                        "error": "Conversation not found"
                    })
                    continue
                
                # Send message
                whatsapp_response = await whatsapp_service.send_text_message(
                    to_number=conversation["customer_phone"],
                    text=message_data.text_content
                )
                
                if whatsapp_response:
                    # Create message record
                    message_dict = {
                        "conversation_id": ObjectId(message_data.conversation_id),
                        "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
                        "type": "text",
                        "direction": "outbound",
                        "sender_role": "agent",
                        "sender_id": current_user.id,
                        "text_content": message_data.text_content,
                        "status": "sent",
                        "timestamp": datetime.now(timezone.utc),
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                        "is_automated": False
                    }
                    
                    result = await db.messages.insert_one(message_dict)
                    
                    results.append({
                        "conversation_id": message_data.conversation_id,
                        "success": True,
                        "message_id": str(result.inserted_id)
                    })
                else:
                    results.append({
                        "conversation_id": message_data.conversation_id,
                        "success": False,
                        "error": "WhatsApp API error"
                    })
                    
            except Exception as e:
                results.append({
                    "conversation_id": message_data.conversation_id,
                    "success": False,
                    "error": str(e)
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to send bulk messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 