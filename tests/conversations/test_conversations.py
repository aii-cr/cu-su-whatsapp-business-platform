import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.core.config import settings
from app.core.logger import logger

@pytest_asyncio.fixture(scope="module")
async def login_token():
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        login_payload = {"email": "pytestuser@example.com", "password": "pytestpassword123"}
        resp = await ac.post(f"{settings.API_PREFIX}/auth/users/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()
        return data["access_token"], data["user"]

@pytest.mark.asyncio
async def test_list_conversations(login_token):
    logger.info("[TEST] Starting test_list_conversations")
    token, _ = login_token
    try:
        async with AsyncClient(base_url=settings.DOMAIN) as ac:
            headers = {"Authorization": f"Bearer {token}"}
            # List all conversations
            resp = await ac.get(f"{settings.API_PREFIX}/conversations/", headers=headers)
            logger.info(f"[TEST] List all conversations status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            assert "conversations" in data
            logger.info(f"[TEST] List all conversations returned {len(data['conversations'])} conversations.")
            # Optionally, test with search param (if you have test data)
            resp2 = await ac.get(f"{settings.API_PREFIX}/conversations/?search=Test", headers=headers)
            logger.info(f"[TEST] List conversations with search param status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert "conversations" in data2
            logger.info(f"[TEST] List conversations with search param returned {len(data2['conversations'])} conversations.")
    except AssertionError as e:
        logger.error(f"[TEST] test_list_conversations failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_list_conversations unexpected error: {e}")
        raise
    logger.info("[TEST] test_list_conversations completed successfully.")

@pytest.mark.asyncio
async def test_get_conversation_by_id(login_token):
    logger.info("[TEST] Starting test_get_conversation_by_id")
    token, _ = login_token
    try:
        async with AsyncClient(base_url=settings.DOMAIN) as ac:
            headers = {"Authorization": f"Bearer {token}"}
            # First, list conversations to get a valid ID
            resp = await ac.get(f"{settings.API_PREFIX}/conversations/", headers=headers)
            logger.info(f"[TEST] List conversations for ID status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            conversations = data.get("conversations", [])
            if not conversations:
                logger.warning("[TEST] No conversations found to test get by ID. Skipping.")
                pytest.skip("No conversations found to test get by ID.")
            conv_id = conversations[0]["id"] if "id" in conversations[0] else conversations[0]["_id"]
            # Get conversation by ID
            resp2 = await ac.get(f"{settings.API_PREFIX}/conversations/{conv_id}", headers=headers)
            logger.info(f"[TEST] Get conversation by ID status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            logger.info(f"[TEST] Conversation by ID response: {data2}")
            assert data2.get("id", data2.get("_id")) == conv_id
            logger.info(f"[TEST] Successfully retrieved conversation with ID: {conv_id}")
    except AssertionError as e:
        logger.error(f"[TEST] test_get_conversation_by_id failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_get_conversation_by_id unexpected error: {e}")
        raise
    logger.info("[TEST] test_get_conversation_by_id completed successfully.") 