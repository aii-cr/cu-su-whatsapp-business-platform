#!/usr/bin/env python3
"""
Local webhook test script.
This helps verify webhook functionality without deploying.
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone
from app.core.config import settings

async def test_webhook_endpoints():
    """Test webhook endpoints locally."""
    
    print("🔍 Local Webhook Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Webhook verification endpoint
    print("\n🧪 Test 1: Webhook Verification Endpoint")
    print("-" * 40)
    
    verify_params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "test_challenge_123"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/whatsapp/webhook", params=verify_params)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200 and response.text == "test_challenge_123":
                print("✅ Webhook verification endpoint working correctly")
            else:
                print("❌ Webhook verification endpoint not working")
                
    except Exception as e:
        print(f"❌ Error testing webhook verification: {str(e)}")
    
    # Test 2: Webhook test endpoint
    print("\n🧪 Test 2: Webhook Test Endpoint")
    print("-" * 40)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/v1/whatsapp/webhook/test")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                print("✅ Webhook test endpoint working correctly")
            else:
                print("❌ Webhook test endpoint not working")
                
    except Exception as e:
        print(f"❌ Error testing webhook test endpoint: {str(e)}")
    
    # Test 3: Simulate webhook payload
    print("\n🧪 Test 3: Simulate Webhook Payload")
    print("-" * 40)
    
    # Simulate a message delivery status webhook
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
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v1/whatsapp/webhook",
                json=webhook_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Webhook payload processing working correctly")
            else:
                print("❌ Webhook payload processing failed")
                
    except Exception as e:
        print(f"❌ Error testing webhook payload: {str(e)}")

async def check_webhook_configuration():
    """Check webhook configuration."""
    
    print("\n\n🔧 Webhook Configuration Check")
    print("=" * 50)
    
    print(f"Webhook URL: {settings.WHATSAPP_WEBHOOK_URL}")
    print(f"Verify Token: {settings.WHATSAPP_VERIFY_TOKEN[:10]}..." if settings.WHATSAPP_VERIFY_TOKEN else "Not set")
    print(f"App Secret: {settings.WHATSAPP_APP_SECRET[:10]}..." if settings.WHATSAPP_APP_SECRET else "Not set")
    print(f"Phone Number ID: {settings.WHATSAPP_PHONE_NUMBER_ID}")
    
    # Check if webhook URL is a placeholder
    if "your-domain.com" in settings.WHATSAPP_WEBHOOK_URL:
        print("\n⚠️  WARNING: Webhook URL is set to placeholder!")
        print("   You need to update WHATSAPP_WEBHOOK_URL in your .env file")
        print("   to point to your actual domain or ngrok URL")
    
    # Check if verify token is set
    if not settings.WHATSAPP_VERIFY_TOKEN or settings.WHATSAPP_VERIFY_TOKEN == "your-webhook-verify-token":
        print("\n⚠️  WARNING: Verify token is not properly configured!")
        print("   Update WHATSAPP_VERIFY_TOKEN in your .env file")

if __name__ == "__main__":
    asyncio.run(test_webhook_endpoints())
    asyncio.run(check_webhook_configuration()) 