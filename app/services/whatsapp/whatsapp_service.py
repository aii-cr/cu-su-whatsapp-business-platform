import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.core.logger import logger

class WhatsAppAPIError(Exception):
    def __init__(self, status_code: int, response_text: str, error_json: dict = None):
        self.status_code = status_code
        self.response_text = response_text
        self.error_json = error_json
        super().__init__(f"WhatsApp API error {status_code}: {response_text}")

class WhatsAppService:
    """Service class for WhatsApp Business API operations."""
    def __init__(self):
        self.base_url = f"{settings.WHATSAPP_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def send_text_message(self, to_number: str, text: str, reply_to_message_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Ensure phone number is in international format
        formatted_number = self._format_phone_number(to_number)
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_number,
            "type": "text",
            "text": {"body": text}
        }
        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}
        logger.info(f"[WHATSAPP_API] Sending text message to {formatted_number} via {url}")
        logger.info(f"[WHATSAPP_API] Request payload: {payload}")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                logger.info(f"[WHATSAPP_API] Response status: {response.status_code}")
                logger.info(f"[WHATSAPP_API] Response body: {response.text}")
                if response.status_code // 100 != 2:
                    try:
                        error_json = response.json()
                    except Exception:
                        error_json = None
                    raise WhatsAppAPIError(response.status_code, response.text, error_json)
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[WHATSAPP_API] HTTP error: {e.response.status_code} - {e.response.text}")
            raise WhatsAppAPIError(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"[WHATSAPP_API] Unexpected error: {str(e)}")
            raise WhatsAppAPIError(-1, str(e))

    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to international format required by WhatsApp API.
        
        Args:
            phone_number: Phone number in any format
            
        Returns:
            Formatted phone number with country code (e.g., "50684716592" -> "50684716592")
        """
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # If it starts with +, remove it (WhatsApp API doesn't expect +)
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        # Ensure it's a valid length (7-15 digits)
        if len(cleaned) < 7 or len(cleaned) > 15:
            logger.warning(f"Phone number {phone_number} may be invalid (length: {len(cleaned)})")
        
        return cleaned

    async def send_template_message(self, to_number: str, template_name: str, language_code: str = "en_US", parameters: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Send a template message via WhatsApp Business API.
        
        Args:
            to_number: Recipient phone number
            template_name: Name of the approved template
            language_code: Template language code (default: en_US)
            parameters: List of parameters for template variables
            
        Returns:
            WhatsApp API response or None if failed
        """
        # Ensure phone number is in international format
        formatted_number = self._format_phone_number(to_number)
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        # Build template payload
        template_payload = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        # Add parameters if provided
        if parameters:
            template_payload["components"] = []
            
            # For the portal_notification template, we know it has 1 header parameter
            # We'll send the first parameter to header, and any remaining to body
            if len(parameters) > 0:
                # Add header component with first parameter
                template_payload["components"].append({
                    "type": "header",
                    "parameters": [parameters[0]]
                })
                
                # Add body component with remaining parameters (if any)
                if len(parameters) > 1:
                    template_payload["components"].append({
                        "type": "body",
                        "parameters": parameters[1:]
                    })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_number,
            "type": "template",
            "template": template_payload
        }
        
        logger.info(f"[WHATSAPP_API] Sending template message '{template_name}' to {formatted_number} via {url}")
        logger.info(f"[WHATSAPP_API] Request payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, headers=self.headers, json=payload)
                logger.info(f"[WHATSAPP_API] Response status: {response.status_code}")
                logger.info(f"[WHATSAPP_API] Response body: {response.text}")
                
                if response.status_code // 100 != 2:
                    try:
                        error_json = response.json()
                    except Exception:
                        error_json = None
                    raise WhatsAppAPIError(response.status_code, response.text, error_json)
                
                response_json = response.json()
                logger.info(f"[WHATSAPP_API] Parsed response: {response_json}")
                return response_json
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[WHATSAPP_API] HTTP error: {e.response.status_code} - {e.response.text}")
            raise WhatsAppAPIError(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"[WHATSAPP_API] Unexpected error: {str(e)}")
            raise WhatsAppAPIError(-1, str(e))

    async def get_message_templates(self) -> List[Dict[str, Any]]:
        logger.info("Pretend to fetch WhatsApp message templates")
        return [] 