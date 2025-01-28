from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.core.logger import logger
from app.core.utils import send_whatsapp_template_message
from datetime import datetime
from app.services.database_service import ChatPlatformService

router = APIRouter()


from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Endpoint for Meta (Facebook) Webhook verification.
    Extracts query parameters from the request object, allowing
    the function to not explicitly require them as arguments.
    """
    query_params = request.query_params

    # Extract required query parameters
    hub_mode = query_params.get("hub.mode")
    hub_challenge = query_params.get("hub.challenge")
    hub_verify_token = query_params.get("hub.verify_token")

    # Perform verification
    if hub_mode and hub_challenge and hub_verify_token:
        if hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("Webhook verified successfully.")
            return int(hub_challenge)
        else:
            logger.warning("Webhook verification failed. Invalid verify token.")
            raise HTTPException(status_code=403, detail="Invalid verification token")
    logger.error("Bad request for webhook verification.")
    raise HTTPException(status_code=400, detail="Missing required query parameters")




@router.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """
    Endpoint to handle WhatsApp webhooks, currently supporting only `messages` field.
    """
    data = await request.json()
    logger.info(f"Incoming WhatsApp webhook data: {data}")

    try:
        # Validate the general payload structure
        if not isinstance(data, dict) or "entry" not in data:
            raise ValueError("Invalid payload structure: Missing 'entry' key")
        
        entry = data["entry"]
        if not isinstance(entry, list) or len(entry) == 0:
            raise ValueError("Invalid payload structure: 'entry' is empty or not a list")
        
        for entry_item in entry:
            changes = entry_item.get("changes", [])
            if not isinstance(changes, list) or len(changes) == 0:
                logger.warning("No changes in entry. Skipping this webhook.")
                continue
            
            for change in changes:
                # Process only `messages` field for now
                field = change.get("field")
                if field != "messages":
                    logger.info(f"Skipping unsupported webhook field: {field}")
                    continue
                
                value = change.get("value", {})
                if not value:
                    raise ValueError("Invalid payload structure: Missing 'value' object")

                # Validate and process the `messages`
                messages = value.get("messages", [])
                if not isinstance(messages, list) or len(messages) == 0:
                    logger.info("No messages found in the webhook. Skipping.")
                    continue

                for message in messages:
                    # Extract required fields
                    msg_id = message.get("id")
                    from_number = message.get("from")
                    timestamp = message.get("timestamp")
                    msg_body = message.get("text", {}).get("body", "")
                    conversation_id = value.get("metadata", {}).get("phone_number_id")  # Example use of `phone_number_id`

                    if not msg_id or not from_number:
                        raise ValueError("Invalid message structure: Missing required fields (id, from)")

                    logger.info(f"Message received: ID={msg_id}, From={from_number}, Body={msg_body}")

                    # Save message to database
                    chat_message = {
                        "conversation_id": conversation_id,
                        "message_id": msg_id,
                        "sender_id": from_number,
                        "sender_role": "customer",
                        "message": msg_body,
                        "timestamp": datetime.utcnow(),
                        "message_type": "text",
                    }
                    await ChatPlatformService.create_message(chat_message)

                    # Send auto-reply using a template
                    send_whatsapp_template_message(
                        to_number=from_number,
                        template_name="hello_world"
                    )

        return {"status": "received"}
    except ValueError as e:
        logger.error(f"Payload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    
# -------------- NEW TEST ENDPOINT --------------

@router.get("/send-test-message")
def send_test_message():
    """
    Simple test endpoint to send a WhatsApp message 
    to the test number 50684716592 using a predefined template.
    """
    to_number = "50684716592"
    template_name = "hello_world"  # Update with a valid, approved template name
    logger.info(f"Sending test message to {to_number} with template '{template_name}'")

    response = send_whatsapp_template_message(
        to_number=to_number,
        template_name=template_name
    )

    if response.status_code == 200:
        return {"detail": "Test message sent successfully", "to": to_number}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
