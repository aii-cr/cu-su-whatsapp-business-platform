import pytest
from httpx import AsyncClient
from app.core.config import settings

# @pytest.mark.asyncio
# async def test_send_message_success():
#     async with AsyncClient(base_url=settings.DOMAIN) as ac:
#         # Login
#         login_payload = {"email": "testuser@example.com", "password": "testpassword123"}
#         login_resp = await ac.post(f"{settings.API_PREFIX}/auth/users/login", json=login_payload)
#         assert login_resp.status_code == 200
#         token = login_resp.json()["access_token"]
#         headers = {"Authorization": f"Bearer {token}"}

#         # Create conversation
#         conversation_payload = {"customer_phone": "+50684716592"}
#         conv_resp = await ac.post(f"{settings.API_PREFIX}/conversations/", json=conversation_payload, headers=headers)
#         assert conv_resp.status_code == 201
#         conversation_id = conv_resp.json()["id"] if "id" in conv_resp.json() else conv_resp.json().get("_id")
#         assert conversation_id

#         # Send message using only customer_phone (should reuse conversation)
#         message_payload = {
#             "customer_phone": "+50684716592",
#             "text_content": "Hello from test!"
#         }
#         msg_resp = await ac.post(f"{settings.API_PREFIX}/messages/send", json=message_payload, headers=headers)
#         assert msg_resp.status_code == 201
#         data = msg_resp.json()
#         assert data["message"]["conversation_id"] == conversation_id
#         assert data["message"]["text_content"] == "Hello from test!"

@pytest.mark.asyncio
async def test_send_message_creates_conversation():
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        # Login
        login_payload = {"email": "testuser@example.com", "password": "testpassword123"}
        login_resp = await ac.post(f"{settings.API_PREFIX}/auth/users/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Send message to a new phone (no prior conversation)
        new_phone = "50684716592"
        message_payload = {
            "customer_phone": new_phone,
            "text_content": "Hello from test!"
        }
        msg_resp = await ac.post(f"{settings.API_PREFIX}/messages/send", json=message_payload, headers=headers)
        assert msg_resp.status_code == 201
        data = msg_resp.json()
        assert data["message"]["text_content"] == "Hello from test!"
        assert data["message"]["conversation_id"] 