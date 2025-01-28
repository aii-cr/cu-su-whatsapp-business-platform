from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.core.logger import logger
from app.core.utils import send_whatsapp_template_message
from datetime import datetime
from app.db.chat_platform_db import mongo
from app.services.database_service import ChatPlatformService

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
            logger.debug(f"Processing entry item: {entry_item}")
            changes = entry_item.get("changes", [])
            if not isinstance(changes, list) or len(changes) == 0:
                logger.warning("No changes in entry. Skipping this webhook.")
                continue
            
            for change in changes:
                logger.debug(f"Processing change: {change}")
                # Process only `messages` field for now
                field = change.get("field")
                if field != "messages":
                    logger.info(f"Skipping unsupported webhook field: {field}")
                    continue
                
                value = change.get("value", {})
                if not value:
                    logger.warning("Missing 'value' object in changes. Skipping.")
                    continue

                logger.debug(f"Value object: {value}")
                # Validate and process the `messages`
                messages = value.get("messages")
                if not messages or not isinstance(messages, list):
                    logger.warning("No valid 'messages' found. Skipping this change.")
                    continue

                for message in messages:
                    # Ensure `message` is a valid dictionary
                    if not isinstance(message, dict):
                        logger.warning(f"Invalid message structure: {message}. Skipping.")
                        continue

                    # Extract required fields
                    msg_id = message.get("id")
                    from_number = message.get("from")
                    timestamp = message.get("timestamp")
                    msg_body = message.get("text", {}).get("body", "")
                    conversation_id = value.get("metadata", {}).get("phone_number_id")  # Example use of `phone_number_id`

                    if not msg_id or not from_number:
                        logger.error("Invalid message structure: Missing required fields (id, from).")
                        continue

                    logger.info(f"Message received: ID={msg_id}, From={from_number}, Body={msg_body}")

                    # Save message to database
                    chat_message = {
                        "conversation_id": conversation_id,
                        "message_id": msg_id,
                        "sender_id": from_number,
                        "sender_role": "customer",
                        "message": msg_body,
                        "timestamp": datetime.now(),
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



@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """
    Retrieve all messages for a given conversation, sorted by timestamp.
    """
    try:
        messages = await ChatPlatformService.get_messages_by_conversation(conversation_id)
        return {"conversation_id": conversation_id, "messages": messages}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error retrieving messages: {e}")
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


@router.get("/test-db")
async def test_db():
    """
    Test the MongoDB connection and list collections.
    """
    try:
        collections = await mongo.db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
