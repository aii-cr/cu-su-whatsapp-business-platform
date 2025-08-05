"""Start conversation with template message endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
import re

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationResponse
from app.services import conversation_service, whatsapp_service, audit_service, websocket_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

class StartConversationRequest(BaseModel):
    """Request model for starting a conversation with template."""
    phone_number: str
    customer_name: Optional[str] = None
    template_name: str
    template_language: str = "en_US"
    template_components: Optional[List[Dict[str, Any]]] = None
    department_id: Optional[str] = None
    priority: str = "normal"
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format with country code."""
        # Remove all non-digit characters
        cleaned = re.sub(r'[^\d]', '', v)
        
        # Must be between 10 and 15 digits (international standard)
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        
        # Must start with country code (not 0 or 1 for most countries)
        if not cleaned[0].isdigit() or cleaned[0] in ['0']:
            raise ValueError('Phone number must include a valid country code')
        
        return cleaned
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority value."""
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {", ".join(valid_priorities)}')
        return v

class StartConversationResponse(BaseModel):
    """Response model for starting a conversation."""
    conversation: ConversationResponse
    message_sent: bool
    whatsapp_message_id: Optional[str] = None
    template_used: str

@router.post("/start", response_model=StartConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation_with_template(
    request_data: StartConversationRequest,
    current_user: User = Depends(require_permissions(["conversations:create", "messages:send_template"]))
):
    """
    Start a new conversation by sending a template message to a customer.
    
    This endpoint:
    1. Validates the phone number format with country code
    2. Checks if conversation already exists for this customer
    3. Creates a new conversation if needed
    4. Sends the specified WhatsApp template message
    5. Creates the message record in the database
    6. Triggers real-time notifications for dashboard
    
    Args:
        request_data: Request data with phone number and template details
        current_user: Current authenticated user
        
    Returns:
        Created conversation and message sending status
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(f"🚀 [START_CONVERSATION] Starting conversation for {request_data.phone_number} with template {request_data.template_name}")
        
        # Check if conversation already exists for this phone number
        existing_conversation = await conversation_service.find_conversation_by_phone(
            request_data.phone_number
        )
        
        if existing_conversation:
            logger.info(f"📋 [START_CONVERSATION] Conversation already exists for {request_data.phone_number}: {existing_conversation['_id']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A conversation already exists for this phone number. Please use the existing conversation."
            )
        
        # Validate template exists and is available
        try:
            templates = await whatsapp_service.get_message_templates()
            template_exists = any(
                template.get('name') == request_data.template_name and 
                template.get('language') == request_data.template_language 
                for template in templates
            )
            
            if not template_exists:
                logger.warning(f"❌ [START_CONVERSATION] Template not found: {request_data.template_name} ({request_data.template_language})")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Template '{request_data.template_name}' in language '{request_data.template_language}' not found or not approved"
                )
                
        except Exception as e:
            logger.error(f"❌ [START_CONVERSATION] Failed to validate template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate template availability"
            )
        
        # Create new conversation
        logger.info(f"📝 [START_CONVERSATION] Creating new conversation for {request_data.phone_number}")
        conversation = await conversation_service.create_conversation(
            customer_phone=request_data.phone_number,
            customer_name=request_data.customer_name,
            department_id=request_data.department_id,
            assigned_agent_id=str(current_user.id),  # Assign to current user
            created_by=str(current_user.id),
            priority=request_data.priority,
            channel="whatsapp",
            customer_type="individual",
            tags=[],
            metadata={
                "initiated_by": "agent",
                "initial_template": request_data.template_name,
                "template_language": request_data.template_language
            }
        )
        
        logger.info(f"✅ [START_CONVERSATION] Created conversation {conversation['_id']}")
        
        # Send template message via WhatsApp
        logger.info(f"📤 [START_CONVERSATION] Sending template message to {request_data.phone_number}")
        
        try:
            # Format phone number for WhatsApp API (ensure it starts with country code)
            formatted_phone = request_data.phone_number
            if not formatted_phone.startswith('+'):
                formatted_phone = f"+{formatted_phone}"
            
            whatsapp_response = await whatsapp_service.send_template_message(
                to_number=formatted_phone,
                template_name=request_data.template_name,
                language_code=request_data.template_language,
                components=request_data.template_components or []
            )
            
            whatsapp_message_id = whatsapp_response.get('messages', [{}])[0].get('id') if whatsapp_response.get('messages') else None
            message_sent = True
            
            logger.info(f"✅ [START_CONVERSATION] Template message sent successfully. WhatsApp ID: {whatsapp_message_id}")
            
        except Exception as e:
            logger.error(f"❌ [START_CONVERSATION] Failed to send template message: {str(e)}")
            # Don't fail the entire request if message sending fails
            whatsapp_message_id = None
            message_sent = False
        
        # Create message record in database if message was sent
        if message_sent and whatsapp_message_id:
            try:
                from app.services import message_service
                
                message = await message_service.create_message(
                    conversation_id=str(conversation["_id"]),
                    message_type="template",
                    direction="outbound",
                    sender_role="agent",
                    sender_id=str(current_user.id),
                    sender_name=current_user.name or current_user.email,
                    text_content=f"Template: {request_data.template_name}",
                    whatsapp_message_id=whatsapp_message_id,
                    whatsapp_data={
                        "messaging_product": "whatsapp",
                        "template_name": request_data.template_name,
                        "template_language": request_data.template_language,
                        "template_components": request_data.template_components
                    },
                    status="sent"
                )
                
                logger.info(f"✅ [START_CONVERSATION] Created message record {message['_id']}")
                
                # Send WebSocket notifications for new message
                await websocket_service.notify_new_message(str(conversation["_id"]), message)
                
            except Exception as e:
                logger.error(f"❌ [START_CONVERSATION] Failed to create message record: {str(e)}")
        
        # Send WebSocket notifications for new conversation
        await websocket_service.notify_new_conversation(conversation)
        await websocket_service.notify_conversation_list_update(conversation, "created")
        
        # Trigger stats update for dashboard
        try:
            stats = await conversation_service.get_conversation_stats()
            await websocket_service.notify_dashboard_stats_update(stats)
        except Exception as e:
            logger.error(f"Failed to update dashboard stats after conversation creation: {str(e)}")
        
        # ===== AUDIT LOGGING =====
        await audit_service.log_conversation_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=str(conversation["_id"]),
            customer_phone=request_data.phone_number,
            customer_name=request_data.customer_name,
            template_used=request_data.template_name,
            message_sent=message_sent,
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [START_CONVERSATION] Successfully started conversation {conversation['_id']} for {request_data.phone_number}")
        
        return StartConversationResponse(
            conversation=ConversationResponse(**conversation),
            message_sent=message_sent,
            whatsapp_message_id=whatsapp_message_id,
            template_used=request_data.template_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [START_CONVERSATION] Error starting conversation: {str(e)}")
        raise handle_database_error(e, "start_conversation", "conversation")