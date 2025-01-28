from fastapi import APIRouter, Request, HTTPException
from app.core.config import settings
from app.core.logger import logger
from app.core.utils import send_whatsapp_template_message, mark_message_as_read_on_whatsapp
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
    Handles incoming WhatsApp messages.
    """
    data = await request.json()
    logger.info(f"Incoming WhatsApp message data: {data}")

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]

        if change["field"] != "messages":
            return {"status": "ignored"}

        value = change["value"]
        business_number = value["metadata"]["display_phone_number"]
        phone_number_id = value["metadata"]["phone_number_id"]

        for message in value.get("messages", []):
            message_id = message["id"]
            from_number = message["from"]
            timestamp = message["timestamp"]
            message_body = message.get("text", {}).get("body", "")

            conversation_id = f"{phone_number_id}_{from_number}"

            chat_message = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "sender_id": from_number,
                "receiver_id": business_number,
                "sender_role": "customer",
                "message": message_body,
                "timestamp": timestamp,
                "message_type": message["type"],
                "status": "received"
            }

            await ChatPlatformService.create_message(chat_message)

            await send_message(business_number, from_number, "hello_world")

            await ChatPlatformService.mark_messages_as_read(conversation_id, from_number)
            
            await mark_message_as_read_on_whatsapp(phone_number_id, message_id)

        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def send_message(business_number: str, customer_number: str, template: str):
    """
    Saves and sends a WhatsApp template message.
    """
    try:
        chat_message = {
            "conversation_id": f"{business_number}_{customer_number}",
            "message_id": f"auto_{datetime.now().timestamp()}",
            "sender_id": business_number,
            "receiver_id": customer_number,
            "sender_role": "business",
            "message": f"Template: {template}",
            "timestamp": int(datetime.now().timestamp()),
            "message_type": "template",
            "status": "sent"
        }

        await ChatPlatformService.create_message(chat_message)
        send_whatsapp_template_message(to_number=customer_number, template_name=template)
    except Exception as e:
        logger.error(f"Error sending message: {e}")

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """
    Retrieves all messages for a conversation in order.
    """
    try:
        messages = await ChatPlatformService.get_messages_by_conversation(conversation_id)
        return {"conversation_id": conversation_id, "messages": messages}
    except HTTPException as e:
        raise e
    
    
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
