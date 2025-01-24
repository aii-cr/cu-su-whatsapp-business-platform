"""
Utility functions for interacting with the WhatsApp Business API.
"""

import requests
from app.core.config import settings
from app.core.logger import logger

WHATSAPP_API_BASE_URL = "https://graph.facebook.com"

def send_whatsapp_template_message(to_number: str, template_name: str, language_code: str = "en_US"):
    """
    Sends a template message via the WhatsApp Business API.
    
    :param to_number: The recipient's phone number in the correct format.
    :param template_name: The name of the pre-registered message template.
    :param language_code: Language code for the template.
    """
    url = f"{WHATSAPP_API_BASE_URL}/v21.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": { "code": language_code }
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"Template message sent to {to_number}: {response.json()}")
    else:
        logger.error(f"Failed to send template message: {response.status_code} - {response.text}")

    return response
