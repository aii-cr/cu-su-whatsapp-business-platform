from fastapi import APIRouter, HTTPException
from app.core.logger import logger
from app.core.utils import send_whatsapp_template_message

router = APIRouter()

@router.get("/send-test-message")
def send_test_message():
    to_number = "50684716592"
    template_name = "hello_world"
    logger.info(f"Sending test message to {to_number} with template '{template_name}'")
    response = send_whatsapp_template_message(
        to_number=to_number,
        template_name=template_name
    )
    if response.status_code == 200:
        return {"detail": "Test message sent successfully", "to": to_number}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text) 