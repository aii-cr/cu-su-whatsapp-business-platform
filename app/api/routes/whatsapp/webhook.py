"""WhatsApp webhook routes for handling inbound messages and status updates."""

from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
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
from app.services.audit.audit_service import AuditService
from app.services.whatsapp.automation_service import automation_service
from app.services import message_service, conversation_service
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
        logger.info(f"Processing webhook {webhook_id} with {len(payload.entry)} entries")
        
        for entry in payload.entry:
            business_account_id = entry.id
            
            for change in entry.changes:
                field = change.get("field", "")
                value = change.get("value", {})
                
                if field == "messages":
                    # Process incoming messages
                    messages = value.get("messages", [])
                    contacts = value.get("contacts", [])
                    
                    for msg_data in messages:
                        try:
                            await process_incoming_message(msg_data, contacts, business_account_id)
                            messages_processed += 1
                        except Exception as e:
                            error_msg = f"Failed to process message {msg_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            processing_errors.append(error_msg)
                
                elif field == "messages":
                    # Process message status updates (sent, delivered, read)
                    statuses = value.get("statuses", [])
                    
                    for status_data in statuses:
                        try:
                            await process_message_status(status_data, business_account_id)
                            statuses_processed += 1
                        except Exception as e:
                            error_msg = f"Failed to process status {status_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            processing_errors.append(error_msg)
                
                else:
                    logger.info(f"Unhandled webhook field: {field}")
        
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
        
        logger.info(f"Webhook {webhook_id} processed: {result.dict()}")
        
    except Exception as e:
        logger.error(f"Critical error processing webhook {webhook_id}: {str(e)}")

async def process_incoming_message(
    message_data: Dict[str, Any], contacts: list, business_account_id: str
):
    """Process a single incoming WhatsApp message."""
    
    # Parse message
    incoming_msg = IncomingMessage(**message_data)
    phone_number = incoming_msg.from_
    
    # Find or create conversation using service
    conversation = await conversation_service.find_conversation_by_phone(phone_number)
    
    if not conversation:
        # Create new conversation
        customer_name = None
        for contact in contacts:
            if contact.get("wa_id") == phone_number:
                profile = contact.get("profile", {})
                customer_name = profile.get("name")
                break
        
        conversation = await conversation_service.create_conversation(
            customer_phone=phone_number,
            customer_name=customer_name
        )
    
    # Create message using service
    message = await message_service.create_message(
        conversation_id=str(conversation["_id"]),
        message_type="text",
        direction="inbound",
        sender_role="customer",
        sender_phone=phone_number,
        sender_name=customer_name,
        text_content=incoming_msg.text.get("body") if incoming_msg.text else None,
        whatsapp_message_id=incoming_msg.id,
        whatsapp_data={
            "messaging_product": "whatsapp",
            "contacts": contacts,
            "display_phone_number": "15551732531"
        },
        status="received"
    )
    
    # Update conversation message count
    await conversation_service.increment_message_count(str(conversation["_id"]))
    
    # Process automation
    await automation_service.process_incoming_message(message)
    
    # Send WebSocket notification
    from app.services.websocket.websocket_service import websocket_service
    await websocket_service.notify_new_message(str(conversation["_id"]), message)
    
    logger.info(f"Processed incoming message {incoming_msg.id} for conversation {conversation['_id']}")

async def process_message_status(
    status_data: Dict[str, Any], business_account_id: str
):
    """Process message status updates."""
    
    status_obj = MessageStatus(**status_data)
    whatsapp_message_id = status_obj.id
    
    # Find message using service
    message = await message_service.find_message_by_whatsapp_id(whatsapp_message_id)
    
    if not message:
        logger.warning(f"Message not found for WhatsApp ID: {whatsapp_message_id}")
        return
    
    # Update message status using service
    await message_service.update_message_status(
        message_id=str(message["_id"]),
        status=status_obj.status,
        whatsapp_data={
            "status": status_obj.status,
            "timestamp": status_obj.timestamp,
            "recipient_id": status_obj.recipient_id,
            "pricing": status_obj.pricing.dict() if status_obj.pricing else None,
            "conversation": status_obj.conversation.dict() if status_obj.conversation else None
        }
    )
    
    logger.info(f"Updated message {whatsapp_message_id} status to {status_obj.status}")

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
        
        # Calculate expected signature
        expected_signature = hmac.new(
            settings.WHATSAPP_APP_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if is_valid:
            logger.info("✅ Webhook signature verified successfully")
        else:
            logger.warning("❌ Invalid webhook signature")
        
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