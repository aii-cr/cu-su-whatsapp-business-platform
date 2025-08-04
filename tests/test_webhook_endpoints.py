import pytest
import httpx
import json
from app.core.config import settings

@pytest.mark.asyncio
async def test_webhook_verification():
    verify_params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "test_challenge_123"
    }
    async with httpx.AsyncClient(base_url=settings.DOMAIN) as client:
        response = await client.get(f"{settings.API_PREFIX}/whatsapp/webhook", params=verify_params)
        assert response.status_code == 200
        assert response.text == "test_challenge_123"

@pytest.mark.asyncio
async def test_webhook_test_endpoint():
    async with httpx.AsyncClient(base_url=settings.DOMAIN) as client:
        response = await client.get(f"{settings.API_PREFIX}/whatsapp/webhook/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "webhook_url" in data

@pytest.mark.asyncio
async def test_webhook_payload_processing():
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID
                            },
                            "statuses": [
                                {
                                    "id": "wamid.HBgLNTA2ODQ3MTY1OTIVAgARGBIyMjEzRDBENzdENjgyRjQ1RTkA",
                                    "status": "delivered",
                                    "timestamp": "1234567890",
                                    "recipient_id": "50684716592"
                                }
                            ]
                        },
                        "field": "message_deliveries"
                    }
                ]
            }
        ]
    }
    async with httpx.AsyncClient(base_url=settings.DOMAIN) as client:
        response = await client.post(
            f"{settings.API_PREFIX}/whatsapp/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        assert "status" in response.json() 