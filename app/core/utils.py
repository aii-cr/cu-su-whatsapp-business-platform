import httpx
import asyncio
from app.core.config import settings
from app.core.logger import logger

WHATSAPP_API_BASE_URL = "https://graph.facebook.com"
WHATSAPP_API_VERSION = "v21.0"  # Update to latest Meta API version
WHATSAPP_ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN

async def send_whatsapp_template_message(to_number: str, template_name: str, language_code: str = "en_US"):
    """
    Sends a template message via the WhatsApp Business API asynchronously.
    
    :param to_number: The recipient's phone number in international format.
    :param template_name: The name of the registered WhatsApp message template.
    :param language_code: Language code for the template (default: "en_US").
    """
    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code}
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                logger.info(f"✅ Template message sent to {to_number}: {response_data}")
                return response_data
            else:
                logger.error(f"❌ Failed to send template message: {response.status_code} - {response.text}")
                return None
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error while sending WhatsApp message: {e}")
            return None


async def mark_message_as_read_on_whatsapp(phone_number_id: str, message_id: str):
    """
    Sends a request to WhatsApp Cloud API to mark a message as 'read' on the customer's device.
    
    :param phone_number_id: The business phone number ID from Meta.
    :param message_id: The message ID of the received message.
    """
    url = f"{WHATSAPP_API_BASE_URL}/{WHATSAPP_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                logger.info(f"✅ Marked message {message_id} as read on WhatsApp.")
                return response_data
            else:
                logger.error(f"❌ Failed to mark message as read: {response.status_code} - {response.text}")
                return None
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error while marking message as read: {e}")
            return None
