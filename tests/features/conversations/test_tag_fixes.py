"""
Test file for tag fixes functionality.
Tests tag unassignment, session expiration, and tag creation edge cases.
Uses the super admin user for authentication.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from bson import ObjectId
from app.core.config import settings
from app.core.logger import logger

@pytest_asyncio.fixture(scope="module")
async def login_token():
    """Get authentication session for super admin user."""
    # Use port 8010 for development server
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    async with AsyncClient(base_url=base_url) as ac:
        login_payload = {"email": "testuser@example.com", "password": "testpassword123"}
        resp = await ac.post(f"{api_prefix}/auth/users/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()
        # Get session cookie from response
        cookies = resp.cookies
        session_cookie = cookies.get("session_token")
        return session_cookie, data

@pytest_asyncio.fixture(scope="module")
async def test_conversation_id(login_token):
    """Get a test conversation ID for tag operations."""
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    async with AsyncClient(base_url=base_url) as ac:
        cookies = {"session_token": session_cookie}
        # Get first available conversation
        resp = await ac.get(f"{api_prefix}/conversations/", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        conversations = data.get("conversations", [])
        if not conversations:
            pytest.skip("No conversations available for testing")
        return conversations[0]["id"] if "id" in conversations[0] else conversations[0]["_id"]

@pytest.mark.asyncio
async def test_tag_unassign_single_click(login_token, test_conversation_id):
    """Test that tag unassignment works with a single click."""
    logger.info("[TEST] Starting test_tag_unassign_single_click")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # First, assign a tag to the conversation
            resp = await ac.get(f"{api_prefix}/tags/suggest?q=&limit=5", cookies=cookies)
            assert resp.status_code == 200
            data = resp.json()
            available_tags = data.get("suggestions", [])
            
            if not available_tags:
                logger.warning("[TEST] No tags available for testing. Skipping.")
                pytest.skip("No tags available for testing.")
            
            # Assign a tag
            tag_id = available_tags[0]["id"]
            assign_data = {
                "tag_ids": [tag_id],
                "auto_assigned": False
            }
            
            resp2 = await ac.post(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign tag status: {resp2.status_code}")
            assert resp2.status_code == 201
            
            # Now unassign the tag
            unassign_data = {
                "tag_ids": [tag_id]
            }
            
            import json
            resp3 = await ac.request(
                "DELETE",
                f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                json=unassign_data,
                cookies=cookies
            )
            logger.info(f"[TEST] Unassign tag status: {resp3.status_code}")
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            # Verify response
            assert "message" in data3
            assert "unassigned_count" in data3
            assert data3["unassigned_count"] == 1
            
            logger.info(f"[TEST] Successfully unassigned tag {tag_id} with single request")
            
            # Verify tag is actually unassigned
            resp4 = await ac.get(f"{api_prefix}/conversations/{test_conversation_id}", cookies=cookies)
            assert resp4.status_code == 200
            data4 = resp4.json()
            
            updated_tags = data4.get("tags", [])
            updated_tag_ids = [tag["id"] for tag in updated_tags]
            
            assert tag_id not in updated_tag_ids, f"Tag {tag_id} still assigned to conversation"
            
            logger.info(f"[TEST] Verified tag {tag_id} is unassigned from conversation")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_tag_unassign_single_click failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_tag_unassign_single_click unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_tag_unassign_single_click completed successfully.")

@pytest.mark.asyncio
async def test_session_expiration_handling():
    """Test that session expiration is handled properly."""
    logger.info("[TEST] Starting test_session_expiration_handling")
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            # Try to access protected endpoint without authentication
            resp = await ac.get(f"{api_prefix}/conversations/")
            logger.info(f"[TEST] Unauthenticated request status: {resp.status_code}")
            assert resp.status_code == 403  # Should return 403 Forbidden
            
            # Try with invalid session cookie
            cookies = {"session_token": "invalid_session_token"}
            resp2 = await ac.get(f"{api_prefix}/conversations/", cookies=cookies)
            logger.info(f"[TEST] Invalid session request status: {resp2.status_code}")
            assert resp2.status_code in [401, 403]  # Should return 401 or 403
            
            logger.info("[TEST] Session expiration handling works correctly")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_session_expiration_handling failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_session_expiration_handling unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_session_expiration_handling completed successfully.")

@pytest.mark.asyncio
async def test_tag_already_exists_handling(login_token, test_conversation_id):
    """Test handling of tag creation when tag already exists."""
    logger.info("[TEST] Starting test_tag_already_exists_handling")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Create a test tag
            tag_name = f"Test Tag {ObjectId()}"
            tag_data = {
                "name": tag_name,
                "color": "#2563eb",
                "category": "general",
                "description": "Test tag for duplicate testing"
            }
            
            resp = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Create tag status: {resp.status_code}")
            assert resp.status_code == 201
            created_tag = resp.json()
            
            # Try to create the same tag again (should fail)
            resp2 = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Duplicate tag creation status: {resp2.status_code}")
            assert resp2.status_code == 400
            data2 = resp2.json()
            assert "already exists" in data2.get("error_message", "").lower()
            
            logger.info("[TEST] Duplicate tag creation correctly rejected")
            
            # Assign the tag to conversation
            assign_data = {
                "tag_ids": [created_tag["id"]],
                "auto_assigned": False
            }
            
            resp3 = await ac.post(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign tag status: {resp3.status_code}")
            assert resp3.status_code == 201
            
            # Try to create a tag with the same name (should fail with different message)
            resp4 = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Tag creation when already assigned status: {resp4.status_code}")
            assert resp4.status_code == 400
            
            logger.info("[TEST] Tag already exists handling works correctly")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_tag_already_exists_handling failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_tag_already_exists_handling unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_tag_already_exists_handling completed successfully.")

@pytest.mark.asyncio
async def test_tag_suggestions_exclude_assigned(login_token, test_conversation_id):
    """Test that tag suggestions exclude already assigned tags."""
    logger.info("[TEST] Starting test_tag_suggestions_exclude_assigned")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Get available tags
            resp = await ac.get(f"{api_prefix}/tags/suggest?q=&limit=10", cookies=cookies)
            assert resp.status_code == 200
            data = resp.json()
            available_tags = data.get("suggestions", [])
            
            if len(available_tags) < 2:
                logger.warning("[TEST] Not enough tags available for testing. Skipping.")
                pytest.skip("Not enough tags available for testing.")
            
            # Assign a tag to the conversation
            tag_to_assign = available_tags[0]
            assign_data = {
                "tag_ids": [tag_to_assign["id"]],
                "auto_assigned": False
            }
            
            resp2 = await ac.post(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign tag status: {resp2.status_code}")
            assert resp2.status_code == 201
            
            # Get suggestions with exclude_ids parameter
            resp3 = await ac.get(f"{api_prefix}/tags/suggest?q=&limit=10&exclude_ids={tag_to_assign['id']}", cookies=cookies)
            logger.info(f"[TEST] Suggestions with exclude status: {resp3.status_code}")
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            # Verify the assigned tag is not in suggestions
            excluded_tag_ids = [tag["id"] for tag in data3["suggestions"]]
            assert tag_to_assign["id"] not in excluded_tag_ids, f"Assigned tag {tag_to_assign['id']} should not appear in suggestions"
            
            logger.info(f"[TEST] Successfully excluded assigned tag from suggestions")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_tag_suggestions_exclude_assigned failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_tag_suggestions_exclude_assigned unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_tag_suggestions_exclude_assigned completed successfully.")
