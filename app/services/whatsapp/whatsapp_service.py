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
            
            # Handle different template structures
            if template_name == "start_conversation":
                # start_conversation has no header parameters, only body parameters
                template_payload["components"].append({
                    "type": "body",
                    "parameters": parameters
                })
            elif template_name == "portal_notification":
                # portal_notification has 1 header parameter and remaining go to body
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
            else:
                # Default behavior: first parameter to header, rest to body
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
        """
        Fetch available WhatsApp message templates from Meta API.
        
        Returns:
            List of template objects with name, language, category, components, etc.
        """
        try:
            # Build the URL for fetching templates
            business_account_id = settings.WHATSAPP_BUSINESS_ID
            url = f"{self.base_url}/{business_account_id}/message_templates"
            
            logger.info(f"[WHATSAPP_API] Fetching templates from {url}")
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers)
                
                logger.info(f"[WHATSAPP_API] Templates response status: {response.status_code}")
                logger.info(f"[WHATSAPP_API] Templates response body: {response.text}")
                
                if response.status_code // 100 != 2:
                    try:
                        error_json = response.json()
                    except Exception:
                        error_json = None
                    raise WhatsAppAPIError(response.status_code, response.text, error_json)
                
                response_data = response.json()
                templates = response_data.get("data", [])
                
                # Parse and format templates for frontend consumption
                formatted_templates = []
                for template in templates:
                    formatted_template = {
                        "id": template.get("id"),
                        "name": template.get("name"),
                        "language": template.get("language"),
                        "status": template.get("status"),
                        "category": template.get("category"),
                        "sub_category": template.get("sub_category"),
                        "parameter_format": template.get("parameter_format"),
                        "components": template.get("components", []),
                        # Extract text content for preview
                        "preview_text": self._extract_template_preview(template.get("components", [])),
                        # Extract parameters for form generation
                        "parameters": self._extract_template_parameters(template.get("components", []))
                    }
                    formatted_templates.append(formatted_template)
                
                logger.info(f"[WHATSAPP_API] Found {len(formatted_templates)} templates")
                return formatted_templates
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[WHATSAPP_API] HTTP error fetching templates: {e.response.status_code} - {e.response.text}")
            raise WhatsAppAPIError(e.response.status_code, e.response.text)
        except Exception as e:
            logger.error(f"[WHATSAPP_API] Unexpected error fetching templates: {str(e)}")
            raise WhatsAppAPIError(-1, str(e))

    def _extract_template_preview(self, components: List[Dict[str, Any]]) -> str:
        """
        Extract preview text from template components.
        
        Args:
            components: List of template components
            
        Returns:
            Preview text for the template
        """
        preview_parts = []
        
        for component in components:
            component_type = component.get("type", "")
            
            if component_type == "HEADER":
                text = component.get("text", "")
                if text:
                    preview_parts.append(f"Header: {text}")
                    
            elif component_type == "BODY":
                text = component.get("text", "")
                if text:
                    # Truncate body text for preview
                    preview_text = text[:100] + "..." if len(text) > 100 else text
                    preview_parts.append(f"Body: {preview_text}")
                    
            elif component_type == "FOOTER":
                text = component.get("text", "")
                if text:
                    preview_parts.append(f"Footer: {text}")
        
        return " | ".join(preview_parts) if preview_parts else "No preview available"

    def _extract_template_parameters(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract parameters from template components for form generation.
        
        Args:
            components: List of template components
            
        Returns:
            List of parameter objects for form inputs
        """
        parameters = []
        
        for component in components:
            component_type = component.get("type", "")
            
            if component_type == "HEADER":
                # Check if header has parameters
                if "example" in component and "header_text" in component["example"]:
                    for i, example in enumerate(component["example"]["header_text"]):
                        parameters.append({
                            "type": "text",
                            "name": f"header_param_{i+1}",
                            "label": f"Header Parameter {i+1}",
                            "example": example,
                            "component": "header",
                            "position": i
                        })
                        
            elif component_type == "BODY":
                # Check if body has parameters (usually {{1}}, {{2}}, etc.)
                text = component.get("text", "")
                import re
                param_matches = re.findall(r'\{\{(\d+)\}\}', text)
                
                for match in param_matches:
                    param_num = int(match)
                    parameters.append({
                        "type": "text",
                        "name": f"body_param_{param_num}",
                        "label": f"Body Parameter {param_num}",
                        "example": f"Parameter {param_num}",
                        "component": "body",
                        "position": param_num - 1
                    })
        
        return parameters 