from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId
from pprint import pformat

from app.core.security import get_current_active_user, require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger, log_conversation_event
from app.schemas.chat.message_in import (
    MessageSend, TemplateMessageSend, MediaMessageSend, 
    InteractiveMessageSend, LocationMessageSend, ContactMessageSend,
    MessageStatusUpdate, BulkMessageSend
)
from app.schemas.chat.message_out import (
    MessageResponse, MessageListResponse, MessageStatsResponse,
    MessageSendResponse, TemplateListResponse
)
from app.db.models.base import PyObjectId
from app.core.utils import send_whatsapp_template_message
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/messages", tags=["messages"])

# Initialize WhatsApp service
whatsapp_service = WhatsAppService()

@router.post("/send", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageSend,
    current_user: User = Depends(require_permissions(["messages:send"]))
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
    from app.core.logger import logger
    
    # ===== REQUEST VALIDATION =====
    logger.info("🔵 [SEND_MESSAGE] Starting message send process")
    logger.info(f"📝 [SEND_MESSAGE] Payload: conversation_id={message_data.conversation_id}, phone={message_data.customer_phone}, text_length={len(message_data.text_content)}")
    logger.info(f"👤 [SEND_MESSAGE] User: {current_user.email} (ID: {current_user.id}, Super Admin: {current_user.is_super_admin})")
    
    try:
        conversation = None
        conversation_id = message_data.conversation_id
        
        # ===== CONVERSATION LOOKUP/CREATION =====
        if not conversation_id and message_data.customer_phone:
            logger.info(f"🔍 [SEND_MESSAGE] Looking up conversation for phone: {message_data.customer_phone}")
            
            conversation = await db.conversations.find_one({
                "customer_phone": message_data.customer_phone,
                "status": {"$in": ["active", "pending"]}
            })
            
            if conversation:
                conversation_id = str(conversation["_id"])
                logger.info(f"✅ [SEND_MESSAGE] Found existing conversation: {conversation_id}")
            else:
                logger.info(f"🆕 [SEND_MESSAGE] Creating new conversation for phone: {message_data.customer_phone}")
                
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
                    logger.info(f"✅ [SEND_MESSAGE] Successfully created conversation: {conversation_id}")
                except Exception as db_error:
                    logger.error(f"❌ [SEND_MESSAGE] Failed to create conversation: {str(db_error)}")
                    if "duplicate key error" in str(db_error).lower():
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="A conversation already exists for this customer"
                        )
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create conversation"
                    )
        
        if not conversation:
            if not conversation_id:
                logger.error("❌ [SEND_MESSAGE] No conversation_id or customer_phone provided")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either conversation_id or customer_phone must be provided."
                )
            
            conversation = await db.conversations.find_one({
                "_id": ObjectId(conversation_id)
            })
            
            if not conversation:
                logger.error(f"❌ [SEND_MESSAGE] Conversation not found: {conversation_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorCode.CONVERSATION_NOT_FOUND
                )
        
        logger.info(f"📋 [SEND_MESSAGE] Using conversation: {conversation_id} (Status: {conversation.get('status')}, Phone: {conversation.get('customer_phone')})")
        
        # ===== PERMISSION CHECK =====
        if (conversation.get("assigned_agent_id") != current_user.id and 
            conversation.get("created_by") != current_user.id and
            not current_user.is_super_admin and
            not await has_permission(current_user, "messages:send_all")):
            logger.warning(f"🚫 [SEND_MESSAGE] Access denied for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CONVERSATION_ACCESS_DENIED
            )
        
        logger.info(f"✅ [SEND_MESSAGE] Permission check passed")
        
        # ===== WHATSAPP API CALL =====
        logger.info(f"📤 [SEND_MESSAGE] Sending WhatsApp message to {conversation['customer_phone']}")
        
        whatsapp_response = await whatsapp_service.send_text_message(
            to_number=conversation["customer_phone"],
            text=message_data.text_content,
            reply_to_message_id=message_data.reply_to_message_id
        )
        
        if not whatsapp_response:
            logger.error(f"❌ [SEND_MESSAGE] WhatsApp API failed for conversation {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR
            )
        
        logger.info(f"✅ [SEND_MESSAGE] WhatsApp API success: {whatsapp_response.get('messages', [{}])[0].get('id', 'unknown')}")
        
        # ===== MESSAGE CREATION =====
        message_dict = {
            "conversation_id": ObjectId(conversation_id),
            "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
            "type": "text",
            "direction": "outbound",
            "sender_role": "agent",
            "sender_id": current_user.id,
            "sender_phone": None,  # Business phone
            "sender_name": current_user.name,
            "text_content": message_data.text_content,
            "status": "sent",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "reply_to_message_id": ObjectId(message_data.reply_to_message_id) if message_data.reply_to_message_id else None,
            "is_automated": False,
            "whatsapp_data": {
                "phone_number_id": whatsapp_response.get("messages", [{}])[0].get("phone_number_id"),
                "business_account_id": whatsapp_response.get("messages", [{}])[0].get("business_account_id")
            }
        }
        
        result = await db.messages.insert_one(message_dict)
        logger.info(f"✅ [SEND_MESSAGE] Message saved to database: {result.inserted_id}")
        
        # ===== CONVERSATION UPDATE =====
        await db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
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
        logger.info(f"✅ [SEND_MESSAGE] Conversation {conversation_id} updated")
        
        # ===== AUDIT LOG =====
        log_conversation_event(
            "message_sent",
            conversation_id,
            message_id=str(result.inserted_id),
            sent_by=str(current_user.id)
        )
        
        # ===== RESPONSE =====
        created_message = await db.messages.find_one({"_id": result.inserted_id})
        logger.info(f"🎉 [SEND_MESSAGE] Successfully completed for conversation {conversation_id}")
        
        return MessageSendResponse(
            message=MessageResponse(**created_message),
            whatsapp_response=whatsapp_response
        )
        
    except HTTPException as he:
        logger.error(f"❌ [SEND_MESSAGE] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ [SEND_MESSAGE] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

@router.post("/template", response_model=MessageSendResponse, status_code=status.HTTP_201_CREATED)
async def send_template_message(
    template_data: TemplateMessageSend,
    current_user: User = Depends(require_permissions(["messages:send_template"]))
):
    """
    Send a template message to a customer.
    Requires 'messages:send_template' permission.
    """
    db = database.db
    
    try:
        # Verify conversation exists
        conversation = await db.conversations.find_one({
            "_id": ObjectId(template_data.conversation_id)
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Send template via WhatsApp API
        whatsapp_response = await whatsapp_service.send_template_message(
            to_number=conversation["customer_phone"],
            template_name=template_data.template_name,
            language_code=template_data.language_code,
            parameters=template_data.parameters
        )
        
        if not whatsapp_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorCode.WHATSAPP_API_ERROR
            )
        
        # Create message record
        message_dict = {
            "conversation_id": ObjectId(template_data.conversation_id),
            "whatsapp_message_id": whatsapp_response.get("messages", [{}])[0].get("id"),
            "type": "template",
            "direction": "outbound",
            "sender_role": "agent",
            "sender_id": current_user.id,
            "sender_phone": None,
            "sender_name": current_user.name,
            "template_data": {
                "name": template_data.template_name,
                "language": template_data.language_code,
                "parameters": template_data.parameters
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
            {"_id": ObjectId(template_data.conversation_id)},
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
        
        # Log template sent
        log_conversation_event(
            "template_sent",
            template_data.conversation_id,
            template_name=template_data.template_name,
            sent_by=str(current_user.id)
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
        logger.error(f"Failed to send template message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

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

@router.get("/conversation/{conversation_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get messages for a specific conversation.
    Requires 'messages:read' permission.
    """
    db = database.db
    
    try:
        # Verify conversation exists and user has access
        conversation = await db.conversations.find_one({
            "_id": ObjectId(conversation_id)
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check access permissions
        if (conversation.get("assigned_agent_id") != current_user.id and 
            not await has_permission(current_user, "messages:read_all")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CONVERSATION_ACCESS_DENIED
            )
        
        # Get messages
        messages = await db.messages.find(
            {"conversation_id": ObjectId(conversation_id)}
        ).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
        
        # Count total
        total = await db.messages.count_documents(
            {"conversation_id": ObjectId(conversation_id)}
        )
        
        return MessageListResponse(
            messages=[MessageResponse(**msg) for msg in messages],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException :
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

@router.get("/templates", response_model=TemplateListResponse)
async def get_available_templates(
    current_user: User = Depends(require_permissions(["messages:read_template"]))
):
    """
    Get available WhatsApp message templates.
    Requires 'messages:read_template' permission.
    """
    try:
        templates = await whatsapp_service.get_message_templates()
        
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

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

async def has_permission(user: User, permission: str) -> bool:
    """
    Check if user has specific permission.
    This is a simplified check - you should implement proper RBAC
    """
    user_roles = await database.db.roles.find(
        {"_id": {"$in": user.role_ids}}
    ).to_list(None)
    
    for role in user_roles:
        role_permissions = await database.db.permissions.find(
            {"_id": {"$in": role.get("permission_ids", [])}}
        ).to_list(None)
        
        for perm in role_permissions:
            if perm.get("key") == permission:
                return True
    
    return False 