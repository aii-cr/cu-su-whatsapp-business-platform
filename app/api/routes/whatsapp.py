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
    Endpoint to receive messages from WhatsApp.
    Logs the data for now, and auto-responds if it's the first message.
    """
    data = await request.json()
    logger.info(f"Incoming WhatsApp message data: {data}")

    # Typically, the payload structure is:
    # {
    #   "entry": [
    #     {
    #       "changes": [
    #         {
    #           "value": {
    #             "messages": [ ... ],
    #             "contacts": [ ... ],
    #             ...
    #           }
    #         }
    #       ]
    #     }
    #   ]
    # }
    # We will do a simple check here, but in production, handle carefully.

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])
        
        if messages:
            for message in messages:
                conversation_id = value["id"]
                from_number = message["from"]
                msg_body = message.get("text", {}).get("body")
                logger.info(f"Received message from {from_number}: {msg_body}")

                # If we want to automatically respond to the first user message, 
                # we could store conversation states in a database or cache.
                # For demonstration, let's just respond to every incoming message once.
                
                # Check message type: e.g., "text", "interactive", etc.
                # For now, let's send a template reply only if it's the first text message.
                # This logic can be improved for real production usage.

                # Simple auto-response with a known template (customize "sample_issue_resolution" or "hello_world").
                
                message = {
                    "conversation_id": conversation_id,
                    "sender_id": from_number,
                    "sender_role": "customer",
                    "message": msg_body,
                    "timestamp": datetime.utcnow(),
                    "message_type": "text",
                }
                await ChatPlatformService.create_message(message)
                send_whatsapp_template_message(
                    to_number=from_number,
                    template_name="hello_world"
                )

        return {"status": "received"}
    except (KeyError, IndexError) as e:
        logger.error(f"Malformed payload structure: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload structure")
    
    
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
