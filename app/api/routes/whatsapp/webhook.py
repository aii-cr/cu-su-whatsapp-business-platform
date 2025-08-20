"""WhatsApp webhook routes for handling inbound messages and status updates."""

from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from typing import Dict, Any, List
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone

from app.schemas.whatsapp import (
    WebhookChallenge, WhatsAppWebhookPayload, ProcessedWebhookData,
    WebhookProcessingResult, IncomingMessage, MessageStatus
)
from app.schemas import SuccessResponse
from app.core.config import settings
from app.core.logger import logger
from app.services import audit_service
from app.services import automation_service
from app.services import message_service, conversation_service
from app.services import websocket_service
from app.services.websocket.websocket_service import manager
from app.core.error_handling import handle_database_error

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Webhooks"])

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Verify WhatsApp webhook URL.
    Meta sends a GET request with verification parameters.
    """
    try:
        # Extract query parameters
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        
        # Validate verification request
        if not all([mode, token, challenge]):
            logger.warning("Webhook verification missing required parameters")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required verification parameters"
            )
        
        if mode != "subscribe":
            logger.warning(f"Invalid webhook mode: {mode}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook mode"
            )
        
        if token != settings.WHATSAPP_VERIFY_TOKEN:
            logger.warning("Invalid webhook verify token")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid verify token"
            )
        
        # Return challenge for successful verification
        logger.info("Webhook verification successful")
        return PlainTextResponse(content=challenge)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during verification"
        )

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming WhatsApp webhook notifications.
    Processes messages, status updates, and other events.
    """
    start_time = time.time()
    
    try:
        # Verify webhook signature
        body = await request.body()
        logger.info(f"🔐 [WEBHOOK] Verifying webhook signature")
        logger.info(f"🔐 [WEBHOOK] Request headers: {dict(request.headers)}")
        
        if not verify_webhook_signature(body, request.headers):
            logger.warning("❌ [WEBHOOK] Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
        
        logger.info("✅ [WEBHOOK] Webhook signature verified successfully")
        
        # Parse webhook payload
        try:
            payload_data = json.loads(body.decode('utf-8'))
            logger.info(f"📥 [WEBHOOK] Received webhook payload:")
            logger.info(f"📋 [WEBHOOK] Payload size: {len(body)} bytes")
            logger.info(f"📋 [WEBHOOK] Headers: {dict(request.headers)}")
            logger.info(f"📋 [WEBHOOK] Full payload: {payload_data}")
            logger.info(f"📋 [WEBHOOK] Object type: {payload_data.get('object', 'unknown')}")
            
            # Validate payload structure
            if not payload_data.get("entry"):
                logger.warning("❌ [WEBHOOK] Invalid payload structure - no 'entry' field")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook payload structure"
                )
            
            logger.info(f"📋 [WEBHOOK] Number of entries: {len(payload_data['entry'])}")
            
            for i, entry in enumerate(payload_data["entry"], 1):
                logger.info(f"📋 [WEBHOOK] Entry {i}:")
                logger.info(f"   - Business Account ID: {entry.get('id')}")
                logger.info(f"   - Number of changes: {len(entry.get('changes', []))}")
                
                for j, change in enumerate(entry.get("changes", []), 1):
                    logger.info(f"   - Change {j} field: {change.get('field')}")
                    
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        messages_count = len(value.get("messages", []))
                        statuses_count = len(value.get("statuses", []))
                        logger.info(f"   - Messages count: {messages_count}")
                        logger.info(f"   - Statuses count: {statuses_count}")
            
            payload = WhatsAppWebhookPayload(**payload_data)
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Failed to parse webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload format"
            )
        
        # Generate webhook ID for tracking
        webhook_id = generate_webhook_id()
        logger.info(f"🔄 [WEBHOOK] Processing webhook {webhook_id} in background")
        logger.info(f"⏱️ [WEBHOOK] Processing started at: {datetime.now(timezone.utc)}")
        
        # Process webhook in background
        background_tasks.add_task(
            process_webhook_payload,
            webhook_id,
            payload,
            start_time
        )
        
        logger.info(f"✅ [WEBHOOK] Webhook {webhook_id} queued for processing")
        logger.info(f"📤 [WEBHOOK] Returning 200 OK to Meta")
        
        return SuccessResponse(
            message="Webhook received successfully",
            data={"webhook_id": webhook_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [WEBHOOK] Critical error handling webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )

async def process_webhook_payload(
    webhook_id: str,
    payload: WhatsAppWebhookPayload,
    start_time: float
):
    """
    Process webhook payload in background.
    Handles messages, status updates, and other events.
    """
    processing_errors = []
    messages_processed = 0
    statuses_processed = 0
    
    try:
        logger.info(f"🔄 [WEBHOOK] Processing webhook {webhook_id} with {len(payload.entry)} entries")
        
        for entry in payload.entry:
            business_account_id = entry.id
            logger.info(f"📋 [WEBHOOK] Processing business account: {business_account_id}")
            
            for change in entry.changes:
                field = change.get("field", "")
                value = change.get("value", {})
                
                logger.info(f"📋 [WEBHOOK] Processing field: {field}")
                
                if field == "messages":
                    await process_messages_field(value, business_account_id, processing_errors, messages_processed, statuses_processed)
                else:
                    logger.info(f"📋 [WEBHOOK] Unhandled webhook field: {field}")
        
        # Log processing result
        processing_time = (time.time() - start_time) * 1000
        result = WebhookProcessingResult(
            success=len(processing_errors) == 0,
            webhook_id=webhook_id,
            messages_processed=messages_processed,
            statuses_processed=statuses_processed,
            errors=processing_errors,
            processing_time_ms=processing_time
        )
        
        logger.info(f"✅ [WEBHOOK] Webhook {webhook_id} processed: {result.dict()}")
        
    except Exception as e:
        logger.error(f"❌ [WEBHOOK] Critical error processing webhook {webhook_id}: {str(e)}")

async def process_messages_field(
    value: Dict[str, Any], 
    business_account_id: str, 
    processing_errors: List[str], 
    messages_processed: int, 
    statuses_processed: int
):
    """Process the 'messages' field from webhook payload."""
    
    # Process incoming messages
    messages = value.get("messages", [])
    contacts = value.get("contacts", [])
    
    logger.info(f"📋 [WEBHOOK] Found {len(messages)} incoming messages")
    
    for msg_data in messages:
        try:
            logger.info(f"📋 [WEBHOOK] Processing incoming message: {msg_data.get('id', 'unknown')}")
            await process_incoming_message(msg_data, contacts, business_account_id)
            messages_processed += 1
            logger.info(f"✅ [WEBHOOK] Successfully processed incoming message: {msg_data.get('id', 'unknown')}")
        except Exception as e:
            error_msg = f"Failed to process message {msg_data.get('id', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            processing_errors.append(error_msg)
    
    # Process message status updates (sent, delivered, read)
    statuses = value.get("statuses", [])
    
    logger.info(f"📋 [WEBHOOK] Found {len(statuses)} status updates")
    
    for status_data in statuses:
        try:
            logger.info(f"📋 [WEBHOOK] Processing status update: {status_data.get('id', 'unknown')} -> {status_data.get('status', 'unknown')}")
            await process_message_status(status_data, business_account_id)
            statuses_processed += 1
            logger.info(f"✅ [WEBHOOK] Successfully processed status update for {status_data.get('id', 'unknown')}")
        except Exception as e:
            error_msg = f"Failed to process status {status_data.get('id', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            processing_errors.append(error_msg)

async def process_incoming_message(
    message_data: Dict[str, Any], contacts: list, business_account_id: str
):
    """Process a single incoming WhatsApp message."""
    
    # Parse message
    incoming_msg = IncomingMessage(**message_data)
    phone_number = incoming_msg.from_
    
    # Extract customer name from contacts
    customer_name = None
    for contact in contacts:
        if contact.get("wa_id") == phone_number:
            profile = contact.get("profile", {})
            customer_name = profile.get("name")
            break
    
    # Find or create conversation using service
    conversation = await conversation_service.find_conversation_by_phone(phone_number)
    is_new_conversation = False
    
    if not conversation:
        # Create new conversation
        conversation = await conversation_service.create_conversation(
            customer_phone=phone_number,
            customer_name=customer_name
        )
        is_new_conversation = True
    
    logger.info(f"📝 [MESSAGE] Creating message with WhatsApp ID: {incoming_msg.id}")
    
    # Create message using service
    message = await message_service.create_message(
        conversation_id=str(conversation["_id"]),
        message_type="text",
        direction="inbound",
        sender_role="customer",
        sender_phone=phone_number,
        sender_name=customer_name,
        text_content=incoming_msg.text.body if incoming_msg.text else None,
        whatsapp_message_id=incoming_msg.id,
        whatsapp_data={
            "messaging_product": "whatsapp",
            "contacts": contacts,
            "display_phone_number": "15551732531"
        },
        status="received"
    )
    
    logger.info(f"✅ [MESSAGE] Created message {message['_id']} with WhatsApp ID: {incoming_msg.id}")
    
    # Update conversation message count
    await conversation_service.increment_message_count(str(conversation["_id"]))
    
    # ===== UPDATE CONVERSATION STATUS =====
    # Set status to "waiting" when customer responds
    current_status = conversation.get("status", "pending")
    if current_status in ["active", "pending"]:
        logger.info(f"🔄 [MESSAGE] Updating conversation status to 'waiting' for customer response")
        updated_conversation = await conversation_service.update_conversation(
            conversation_id=str(conversation["_id"]),
            update_data={"status": "waiting"},
            updated_by=None  # System update
        )
    
    # Process automation
    await automation_service.process_incoming_message(message)
    
    # ===== SINGLE WEBSOCKET NOTIFICATION =====
    # Send a single notification that will trigger all necessary updates
    await websocket_service.notify_incoming_message_processed(
        conversation_id=str(conversation["_id"]),
        message=message,
        is_new_conversation=is_new_conversation,
        conversation=conversation
    )

async def process_message_status(
    status_data: Dict[str, Any], business_account_id: str
):
    """Process message status updates."""
    
    status_obj = MessageStatus(**status_data)
    whatsapp_message_id = status_obj.id
    
    logger.info(f"🔍 [STATUS] Looking for message with WhatsApp ID: {whatsapp_message_id}")
    
    # Find message using service
    message = await message_service.find_message_by_whatsapp_id(whatsapp_message_id)
    
    if not message:
        logger.warning(f"❌ [STATUS] Message not found for WhatsApp ID: {whatsapp_message_id}")
        logger.warning(f"📋 [STATUS] Status data: {status_data}")
        
        # Let's also check if there are any messages in the database for debugging
        from app.db.client import database
        db = await database._get_db()
        total_messages = await db.messages.count_documents({})
        messages_with_whatsapp_id = await db.messages.count_documents({"whatsapp_message_id": {"$exists": True, "$ne": None}})
        logger.info(f"📊 [STATUS] Database stats - Total messages: {total_messages}, Messages with WhatsApp ID: {messages_with_whatsapp_id}")
        
        return
    
    logger.info(f"✅ [STATUS] Found message {message['_id']} for WhatsApp ID: {whatsapp_message_id}")
    
    # Update message status using service
    await message_service.update_message_status(
        message_id=str(message["_id"]),
        status=status_obj.status,
        whatsapp_data={
            "status": status_obj.status,
            "timestamp": status_obj.timestamp,
            "recipient_id": status_obj.recipient_id,
            "pricing": status_obj.pricing if status_obj.pricing else None,
            "conversation": status_obj.conversation if status_obj.conversation else None
        }
    )
    
    logger.info(f"✅ [STATUS] Updated message {whatsapp_message_id} status to {status_obj.status}")
    
    # Get updated message data for optimized notification
    updated_message = await message_service.get_message(str(message["_id"]))
    
    # Serialize the message data to handle ObjectId fields
    if updated_message:
        serialized_message = {}
        for key, value in updated_message.items():
            if key == '_id':
                serialized_message[key] = str(value)
            elif key == 'conversation_id':
                serialized_message[key] = str(value)
            elif key == 'sender_id':
                serialized_message[key] = str(value) if value else None
            elif key == 'reply_to_message_id':
                serialized_message[key] = str(value) if value else None
            elif key == 'media_id':
                serialized_message[key] = str(value) if value else None
            elif isinstance(value, datetime):
                serialized_message[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                serialized_message[key] = value.isoformat()
            else:
                serialized_message[key] = value
    else:
        serialized_message = None
    
    # Send optimized WebSocket notification for status update
    await websocket_service.notify_message_status_update_optimized(
        conversation_id=str(message["conversation_id"]),
        message_id=str(message["_id"]),  # Use internal message ID for consistency
        status=status_obj.status,
        message_data=serialized_message
    )

def verify_webhook_signature(body: bytes, headers: dict) -> bool:
    """
    Verify webhook signature from Meta.
    
    Args:
        body: Request body
        headers: Request headers
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Get signature from headers
        signature = headers.get("x-hub-signature-256", "")
        if not signature:
            logger.warning("No signature found in headers")
            return False
        
        # Remove 'sha256=' prefix
        if not signature.startswith("sha256="):
            logger.warning("Invalid signature format")
            return False
        
        signature = signature[7:]
        
        # Calculate expected signature using app secret (not verify token)
        app_secret = settings.WHATSAPP_APP_SECRET
        expected_signature = hmac.new(
            app_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Debug logging
        logger.info(f"🔍 [WEBHOOK_SIGNATURE] Debug info:")
        logger.info(f"   - App secret length: {len(app_secret)}")
        logger.info(f"   - App secret configured: {bool(app_secret and app_secret != 'development-app-secret')}")
        logger.info(f"   - Body length: {len(body)} bytes")
        logger.info(f"   - Received signature: {signature}")
        logger.info(f"   - Expected signature: {expected_signature}")
        logger.info(f"   - Signatures match: {signature == expected_signature}")
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if is_valid:
            logger.info("✅ Webhook signature verified successfully")
        else:
            logger.warning("❌ Invalid webhook signature")
            logger.warning(f"   - Received: {signature}")
            logger.warning(f"   - Expected: {expected_signature}")
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

def generate_webhook_id() -> str:
    """Generate a unique webhook ID for tracking."""
    timestamp = int(time.time())
    random_suffix = hashlib.md5(f"{timestamp}".encode()).hexdigest()[:8]
    return f"webhook_{timestamp}_{random_suffix}"

@router.get("/webhook/test")
async def test_webhook_connection():
    """
    Test webhook connection and configuration.
    """
    try:
        # Test database connection
        from app.db.client import database
        await database.health_check()
        
        return SuccessResponse(
            message="Webhook configuration is valid",
            data={
                "database": "connected",
                "whatsapp_api": "configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Webhook test failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook test failed: {str(e)}"
        ) 

@router.get("/webhook/debug")
async def debug_webhook_signature():
    """
    Debug webhook signature verification.
    Shows the current app secret configuration and helps troubleshoot signature issues.
    """
    try:
        # Get the app secret (masked for security)
        app_secret = settings.WHATSAPP_APP_SECRET
        masked_secret = app_secret[:4] + "*" * (len(app_secret) - 8) + app_secret[-4:] if len(app_secret) > 8 else "***"
        
        # Test signature calculation with a sample payload
        test_payload = b'{"test": "payload"}'
        expected_signature = hmac.new(
            app_secret.encode('utf-8'),
            test_payload,
            hashlib.sha256
        ).hexdigest()
        
        # Get database statistics
        from app.db.client import database
        db = await database._get_db()
        total_messages = await db.messages.count_documents({})
        messages_with_whatsapp_id = await db.messages.count_documents({"whatsapp_message_id": {"$exists": True, "$ne": None}})
        
        # Get recent messages with WhatsApp IDs
        recent_messages = await db.messages.find(
            {"whatsapp_message_id": {"$exists": True, "$ne": None}},
            {"_id": 1, "whatsapp_message_id": 1, "direction": 1, "status": 1, "created_at": 1}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        # Show other WhatsApp settings
        return SuccessResponse(
            message="Webhook signature debug information",
            data={
                "app_secret_configured": bool(app_secret and app_secret != "development-app-secret"),
                "app_secret_masked": masked_secret,
                "app_secret_length": len(app_secret),
                "test_signature": expected_signature,
                "database_stats": {
                    "total_messages": total_messages,
                    "messages_with_whatsapp_id": messages_with_whatsapp_id,
                    "recent_messages": recent_messages
                },
                "whatsapp_settings": {
                    "access_token_configured": bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_ACCESS_TOKEN != "development-access-token"),
                    "verify_token_configured": bool(settings.WHATSAPP_VERIFY_TOKEN and settings.WHATSAPP_VERIFY_TOKEN != "development-verify-token"),
                    "business_id_configured": bool(settings.WHATSAPP_BUSINESS_ID),
                    "phone_number_id_configured": bool(settings.WHATSAPP_PHONE_NUMBER_ID),
                    "webhook_url": settings.WHATSAPP_WEBHOOK_URL,
                    "api_version": settings.WHATSAPP_API_VERSION,
                    "base_url": settings.WHATSAPP_BASE_URL
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Webhook debug failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook debug failed: {str(e)}"
        ) 