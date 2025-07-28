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
from app.db.client import database
from app.core.logger import logger
from app.services.whatsapp.automation_service import automation_service

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
        if not verify_webhook_signature(body, request.headers):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        try:
            payload_data = json.loads(body.decode('utf-8'))
            webhook_payload = WhatsAppWebhookPayload(**payload_data)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload format"
            )
        
        # Process webhook in background
        webhook_id = generate_webhook_id()
        background_tasks.add_task(
            process_webhook_payload,
            webhook_id,
            webhook_payload,
            start_time
        )
        
        # Return 200 immediately for Meta
        return {"status": "received"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
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
    db = database.db
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
                            await process_incoming_message(
                                db, msg_data, contacts, business_account_id
                            )
                            messages_processed += 1
                        except Exception as e:
                            error_msg = f"Failed to process message {msg_data.get('id', 'unknown')}: {str(e)}"
                            logger.error(error_msg)
                            processing_errors.append(error_msg)
                
                elif field == "message_deliveries" or field == "message_reads":
                    # Process message status updates
                    statuses = value.get("statuses", [])
                    
                    for status_data in statuses:
                        try:
                            await process_message_status(
                                db, status_data, business_account_id
                            )
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
        
        # Store processing result for audit
        await db.webhook_logs.insert_one({
            "webhook_id": webhook_id,
            "result": result.dict(),
            "processed_at": datetime.now(timezone.utc)
        })
        
    except Exception as e:
        logger.error(f"Critical error processing webhook {webhook_id}: {str(e)}")

async def process_incoming_message(
    db, message_data: Dict[str, Any], contacts: list, business_account_id: str
):
    """Process a single incoming WhatsApp message."""
    
    # Parse message
    incoming_msg = IncomingMessage(**message_data)
    phone_number = incoming_msg.from_
    
    # Find or create conversation
    conversation = await db.conversations.find_one({
        "customer_phone": phone_number,
        "status": {"$in": ["active", "pending"]}
    })
    
    if not conversation:
        # Create new conversation
        customer_name = None
        for contact in contacts:
            if contact.get("wa_id") == phone_number:
                profile = contact.get("profile", {})
                customer_name = profile.get("name")
                break
        
        conversation_data = {
            "customer_phone": phone_number,
            "customer_name": customer_name,
            "customer_type": "b2c",  # Default
            "status": "active",
            "priority": "normal",
            "channel": "whatsapp",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_message_at": datetime.now(timezone.utc),
            "message_count": 0,
            "unread_count": 0,
            "tags": [],
            "metadata": {
                "business_account_id": business_account_id,
                "phone_number_id": message_data.get("metadata", {}).get("phone_number_id")
            }
        }
        
        result = await db.conversations.insert_one(conversation_data)
        conversation_id = result.inserted_id
        
        logger.info(f"Created new conversation {conversation_id} for {phone_number}")
    else:
        conversation_id = conversation["_id"]
    
    # Prepare message content based on type
    content = {}
    if incoming_msg.text:
        content = {"text": incoming_msg.text.body}
    elif incoming_msg.image:
        content = {
            "media_id": incoming_msg.image.id,
            "mime_type": incoming_msg.image.mime_type,
            "caption": incoming_msg.image.caption
        }
    elif incoming_msg.audio:
        content = {
            "media_id": incoming_msg.audio.id,
            "mime_type": incoming_msg.audio.mime_type,
            "voice": incoming_msg.audio.voice
        }
    elif incoming_msg.video:
        content = {
            "media_id": incoming_msg.video.id,
            "mime_type": incoming_msg.video.mime_type,
            "caption": incoming_msg.video.caption
        }
    elif incoming_msg.document:
        content = {
            "media_id": incoming_msg.document.id,
            "mime_type": incoming_msg.document.mime_type,
            "filename": incoming_msg.document.filename
        }
    elif incoming_msg.location:
        content = {
            "latitude": incoming_msg.location.latitude,
            "longitude": incoming_msg.location.longitude,
            "name": incoming_msg.location.name,
            "address": incoming_msg.location.address
        }
    elif incoming_msg.contacts:
        content = {"contacts": incoming_msg.contacts.contacts}
    elif incoming_msg.interactive:
        content = {
            "type": incoming_msg.interactive.type,
            "button_reply": incoming_msg.interactive.button_reply,
            "list_reply": incoming_msg.interactive.list_reply
        }
    
    # Create message record
    message_data = {
        "conversation_id": conversation_id,
        "whatsapp_message_id": incoming_msg.id,
        "type": incoming_msg.type,
        "direction": "inbound",
        "sender_role": "customer",
        "content": content,
        "text_content": content.get("text") if content and "text" in content else None,
        "status": "received",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata": {
            "business_account_id": business_account_id,
            "phone_number_id": message_data.get("metadata", {}).get("phone_number_id")
        }
    }
    
    # Add reply context if present
    if incoming_msg.context:
        message_data["reply_to_message_id"] = await find_message_by_whatsapp_id(
            db, incoming_msg.context.id
        )
    
    # Insert message
    await db.messages.insert_one(message_data)
    
    # Update conversation
    await db.conversations.update_one(
        {"_id": conversation_id},
        {
            "$set": {
                "last_message_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            },
            "$inc": {
                "message_count": 1,
                "unread_count": 1
            }
        }
    )
    
    # Process automation (welcome messages, keyword triggers, etc.)
    await automation_service.process_incoming_message(message_data)
    
    # Notify connected clients via WebSocket
    try:
        from app.services.websocket.websocket_service import websocket_service
        await websocket_service.notify_new_message(str(conversation_id), message_data)
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {str(e)}")
    
    logger.info(f"Processed incoming message {incoming_msg.id} for conversation {conversation_id}")

async def process_message_status(
    db, status_data: Dict[str, Any], business_account_id: str
):
    """Process a message status update."""
    
    message_status = MessageStatus(**status_data)
    
    # Find message by WhatsApp ID
    message = await db.messages.find_one({
        "whatsapp_message_id": message_status.id
    })
    
    if not message:
        logger.warning(f"Message not found for status update: {message_status.id}")
        return
    
    # Update message status
    update_data = {
        "status": message_status.status,
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Add error information if status is failed
    if message_status.status == "failed" and message_status.errors:
        error = message_status.errors[0]
        update_data["error_code"] = str(error.get("code", ""))
        update_data["error_message"] = error.get("title", "")
    
    await db.messages.update_one(
        {"_id": message["_id"]},
        {"$set": update_data}
    )
    
    logger.info(f"Updated message {message_status.id} status to {message_status.status}")

def verify_webhook_signature(body: bytes, headers: dict) -> bool:
    """
    Verify WhatsApp webhook signature.
    Meta signs the payload with the app secret.
    """
    signature = headers.get("x-hub-signature-256", "")
    if not signature:
        logger.warning("No webhook signature found in headers")
        return False
    
    # Remove 'sha256=' prefix
    signature = signature.replace("sha256=", "")
    
    # Check if app secret is properly configured
    if not settings.WHATSAPP_APP_SECRET or settings.WHATSAPP_APP_SECRET == "development-app-secret":
        logger.warning("WHATSAPP_APP_SECRET not properly configured. Skipping signature verification.")
        return True  # Allow in development mode
    
    # Calculate expected signature
    expected_signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning(f"Invalid webhook signature. Expected: {expected_signature}, Received: {signature}")
    
    return is_valid

def generate_webhook_id() -> str:
    """Generate unique webhook processing ID."""
    import uuid
    return f"webhook_{int(time.time())}_{str(uuid.uuid4())[:8]}"

async def find_message_by_whatsapp_id(db, whatsapp_message_id: str):
    """Find message by WhatsApp message ID."""
    message = await db.messages.find_one({
        "whatsapp_message_id": whatsapp_message_id
    })
    return message["_id"] if message else None

@router.get("/webhook/test")
async def test_webhook_connection():
    """
    Test endpoint to verify webhook is accessible.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webhook_url": f"{settings.WHATSAPP_WEBHOOK_URL}/webhook",
        "verify_token_configured": bool(settings.WHATSAPP_VERIFY_TOKEN)
    } 