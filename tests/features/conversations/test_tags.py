"""
Test file for tags functionality.
Tests tag creation, suggestions, assignment, and unassignment.
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
async def test_get_tag_suggestions(login_token):
    """Test tag suggestions endpoint."""
    logger.info("[TEST] Starting test_get_tag_suggestions")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test empty query (should return popular tags)
            resp = await ac.get(f"{api_prefix}/tags/suggest?q=&limit=10", cookies=cookies)
            logger.info(f"[TEST] Empty query suggestions status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)
            logger.info(f"[TEST] Empty query returned {len(data['suggestions'])} suggestions")
            
            # Test with search query
            resp2 = await ac.get(f"{api_prefix}/tags/suggest?q=follow&limit=5", cookies=cookies)
            logger.info(f"[TEST] Search query suggestions status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert "suggestions" in data2
            assert isinstance(data2["suggestions"], list)
            logger.info(f"[TEST] Search query returned {len(data2['suggestions'])} suggestions")
            
            # Test with exclude_ids parameter
            if data2["suggestions"]:
                exclude_id = data2["suggestions"][0]["id"]
                resp3 = await ac.get(f"{api_prefix}/tags/suggest?q=follow&limit=5&exclude_ids={exclude_id}", cookies=cookies)
                logger.info(f"[TEST] Exclude IDs suggestions status: {resp3.status_code}")
                assert resp3.status_code == 200
                data3 = resp3.json()
                assert "suggestions" in data3
                # Should not contain the excluded tag
                excluded_ids = [tag["id"] for tag in data3["suggestions"]]
                assert exclude_id not in excluded_ids
                logger.info(f"[TEST] Exclude IDs returned {len(data3['suggestions'])} suggestions")
                
    except AssertionError as e:
        logger.error(f"[TEST] test_get_tag_suggestions failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_get_tag_suggestions unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_get_tag_suggestions completed successfully.")

@pytest.mark.asyncio
async def test_create_tag(login_token):
    """Test tag creation endpoint."""
    logger.info("[TEST] Starting test_create_tag")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test creating a new tag
            tag_data = {
                "name": f"Test Tag {ObjectId()}",
                "color": "#2563eb",
                "category": "general",
                "description": "Test tag for automated testing"
            }
            
            resp = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Create tag status: {resp.status_code}")
            assert resp.status_code == 201
            data = resp.json()
            
            # Verify response structure
            assert "id" in data
            assert data["name"] == tag_data["name"]
            assert data["color"] == tag_data["color"]
            assert data["category"] == tag_data["category"]
            assert data["status"] == "active"
            assert data["is_system_tag"] == False
            
            logger.info(f"[TEST] Successfully created tag: {data['name']} (ID: {data['id']})")
            
            # Test creating duplicate tag (should fail)
            resp2 = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Duplicate tag creation status: {resp2.status_code}")
            assert resp2.status_code == 400
            data2 = resp2.json()
            assert "already exists" in data2.get("error_message", "").lower()
            logger.info("[TEST] Duplicate tag creation correctly rejected")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_create_tag failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_create_tag unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_create_tag completed successfully.")

@pytest.mark.asyncio
async def test_assign_tags_to_conversation(login_token, test_conversation_id):
    """Test assigning tags to a conversation."""
    logger.info("[TEST] Starting test_assign_tags_to_conversation")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # First, get available tags
            resp = await ac.get(f"{api_prefix}/tags/suggest?q=&limit=5", cookies=cookies)
            assert resp.status_code == 200
            data = resp.json()
            available_tags = data.get("suggestions", [])
            
            if not available_tags:
                logger.warning("[TEST] No tags available for assignment test. Skipping.")
                pytest.skip("No tags available for assignment test.")
            
            # Select first two tags for assignment
            tag_ids = [available_tags[0]["id"]]
            if len(available_tags) > 1:
                tag_ids.append(available_tags[1]["id"])
            
            # Assign tags to conversation
            assign_data = {
                "tag_ids": tag_ids,
                "auto_assigned": False
            }
            
            resp2 = await ac.post(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign tags status: {resp2.status_code}")
            assert resp2.status_code == 201  # 201 Created for resource creation
            data2 = resp2.json()
            
            # Verify response - might be empty if tags already assigned
            assert isinstance(data2, list)
            logger.info(f"[TEST] Assignment response: {len(data2)} tags assigned")
            
            logger.info(f"[TEST] Successfully processed tag assignment request")
            
            # Verify tags are actually assigned by getting conversation tags
            resp3 = await ac.get(f"{api_prefix}/conversations/{test_conversation_id}/tags", cookies=cookies)
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            # Check if tags are in conversation tags response
            assigned_tag_ids = [ct["tag"]["id"] for ct in data3]
            
            # Verify that at least one of the requested tags is assigned
            assigned_count = sum(1 for tag_id in tag_ids if tag_id in assigned_tag_ids)
            assert assigned_count > 0, f"None of the requested tags {tag_ids} are assigned to conversation"
            
            logger.info(f"[TEST] Verified {assigned_count} out of {len(tag_ids)} requested tags are assigned to conversation")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_assign_tags_to_conversation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_assign_tags_to_conversation unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_assign_tags_to_conversation completed successfully.")

@pytest.mark.asyncio
async def test_unassign_tags_from_conversation(login_token, test_conversation_id):
    """Test unassigning tags from a conversation."""
    logger.info("[TEST] Starting test_unassign_tags_from_conversation")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # First, get current conversation tags
            resp = await ac.get(f"{api_prefix}/conversations/{test_conversation_id}", cookies=cookies)
            assert resp.status_code == 200
            data = resp.json()
            current_tags = data.get("tags", [])
            
            if not current_tags:
                logger.warning("[TEST] No tags assigned to conversation for unassignment test. Skipping.")
                pytest.skip("No tags assigned to conversation for unassignment test.")
            
            # Select first tag for unassignment
            tag_to_unassign = current_tags[0]["tag"]["id"]
            
            # Unassign tag from conversation
            unassign_data = {
                "tag_ids": [tag_to_unassign]
            }
            
            resp2 = await ac.delete(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=unassign_data, cookies=cookies)
            logger.info(f"[TEST] Unassign tag status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            
            # Verify response
            assert "message" in data2
            assert "unassigned_count" in data2
            assert data2["unassigned_count"] == 1
            
            logger.info(f"[TEST] Successfully unassigned tag {tag_to_unassign}")
            
            # Verify tag is actually unassigned
            resp3 = await ac.get(f"{api_prefix}/conversations/{test_conversation_id}", cookies=cookies)
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            updated_tags = data3.get("tags", [])
            updated_tag_ids = [ct["tag"]["id"] for ct in updated_tags]
            
            assert tag_to_unassign not in updated_tag_ids, f"Tag {tag_to_unassign} still assigned to conversation"
            
            logger.info(f"[TEST] Verified tag {tag_to_unassign} is unassigned from conversation")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_unassign_tags_from_conversation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_unassign_tags_from_conversation unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_unassign_tags_from_conversation completed successfully.")

@pytest.mark.asyncio
async def test_get_tag_settings(login_token):
    """Test getting tag settings."""
    logger.info("[TEST] Starting test_get_tag_settings")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            resp = await ac.get(f"{api_prefix}/tags/settings", cookies=cookies)
            logger.info(f"[TEST] Get tag settings status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            
            # Verify response structure
            assert "max_tags_per_conversation" in data
            assert isinstance(data["max_tags_per_conversation"], int)
            assert data["max_tags_per_conversation"] > 0
            
            logger.info(f"[TEST] Tag settings: max_tags_per_conversation = {data['max_tags_per_conversation']}")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_get_tag_settings failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_get_tag_settings unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_get_tag_settings completed successfully.")

@pytest.mark.asyncio
async def test_list_tags(login_token):
    """Test listing tags with various filters."""
    logger.info("[TEST] Starting test_list_tags")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test basic listing
            resp = await ac.get(f"{api_prefix}/tags/?limit=10", cookies=cookies)
            logger.info(f"[TEST] List tags status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            
            assert "tags" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data
            assert isinstance(data["tags"], list)
            assert isinstance(data["total"], int)
            
            logger.info(f"[TEST] List tags returned {len(data['tags'])} tags, total: {data['total']}")
            
            # Test with search filter
            resp2 = await ac.get(f"{api_prefix}/tags/?search=follow&limit=5", cookies=cookies)
            logger.info(f"[TEST] List tags with search status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            
            assert "tags" in data2
            assert isinstance(data2["tags"], list)
            
            # Verify search results contain search term
            for tag in data2["tags"]:
                assert "follow" in tag["name"].lower() or "follow" in tag.get("display_name", "").lower()
            
            logger.info(f"[TEST] Search returned {len(data2['tags'])} matching tags")
            
            # Test with category filter
            resp3 = await ac.get(f"{api_prefix}/tags/?category=general&limit=5", cookies=cookies)
            logger.info(f"[TEST] List tags with category filter status: {resp3.status_code}")
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            assert "tags" in data3
            assert isinstance(data3["tags"], list)
            
            # Verify all returned tags have the specified category
            for tag in data3["tags"]:
                assert tag["category"] == "general"
            
            logger.info(f"[TEST] Category filter returned {len(data3['tags'])} general tags")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_list_tags failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_list_tags unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_list_tags completed successfully.")

@pytest.mark.asyncio
async def test_create_and_assign_tag_on_the_fly(login_token, test_conversation_id):
    """Test creating a new tag and immediately assigning it to a conversation."""
    logger.info("[TEST] Starting test_create_and_assign_tag_on_the_fly")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # First, create a new tag
            tag_name = f"Test Tag {ObjectId()}"
            tag_data = {
                "name": tag_name,
                "color": "#2563eb",
                "category": "general",
                "description": "Test tag for on-the-fly creation"
            }
            
            resp = await ac.post(f"{api_prefix}/tags/", json=tag_data, cookies=cookies)
            logger.info(f"[TEST] Create tag status: {resp.status_code}")
            assert resp.status_code == 201
            created_tag = resp.json()
            tag_id = created_tag["id"]
            
            logger.info(f"[TEST] Successfully created tag: {tag_name} (ID: {tag_id})")
            
            # Now assign the newly created tag to the conversation
            assign_data = {
                "tag_ids": [tag_id],
                "auto_assigned": False
            }
            
            resp2 = await ac.post(f"{api_prefix}/conversations/{test_conversation_id}/tags", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign newly created tag status: {resp2.status_code}")
            assert resp2.status_code == 201  # Should be 201 for creation
            data2 = resp2.json()
            
            # Verify response
            assert isinstance(data2, list)
            assert len(data2) == 1
            assert data2[0]["tag"]["id"] == tag_id
            assert data2[0]["tag"]["name"] == tag_name
            
            logger.info(f"[TEST] Successfully assigned newly created tag to conversation")
            
            # Verify tag is actually assigned by getting conversation tags
            resp3 = await ac.get(f"{api_prefix}/conversations/{test_conversation_id}/tags", cookies=cookies)
            assert resp3.status_code == 200
            data3 = resp3.json()
            
            # Check if tag is in conversation tags response
            assigned_tag_ids = [ct["tag"]["id"] for ct in data3]
            
            assert tag_id in assigned_tag_ids, f"Newly created tag {tag_id} not found in conversation tags"
            
            logger.info(f"[TEST] Verified newly created tag is assigned to conversation")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_create_and_assign_tag_on_the_fly failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_create_and_assign_tag_on_the_fly unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_create_and_assign_tag_on_the_fly completed successfully.")

@pytest.mark.asyncio
async def test_tag_error_handling(login_token):
    """Test error handling for invalid tag operations."""
    logger.info("[TEST] Starting test_tag_error_handling")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test creating tag with invalid data
            invalid_tag_data = {
                "name": "",  # Empty name should fail
                "color": "invalid-color",  # Invalid color
                "category": "invalid-category"  # Invalid category
            }
            
            resp = await ac.post(f"{api_prefix}/tags/", json=invalid_tag_data, cookies=cookies)
            logger.info(f"[TEST] Invalid tag creation status: {resp.status_code}")
            assert resp.status_code == 422  # Validation error
            
            # Test assigning non-existent tag
            fake_conversation_id = str(ObjectId())
            fake_tag_id = str(ObjectId())
            
            assign_data = {
                "tag_ids": [fake_tag_id],
                "auto_assigned": False
            }
            
            resp2 = await ac.post(f"{api_prefix}/conversations/{fake_conversation_id}/tags/assign", 
                                json=assign_data, cookies=cookies)
            logger.info(f"[TEST] Assign non-existent tag status: {resp2.status_code}")
            assert resp2.status_code in [404, 400]  # Should fail
            
            # Test unassigning from non-existent conversation
            resp3 = await ac.post(f"{api_prefix}/conversations/{fake_conversation_id}/tags/unassign", 
                                json={"tag_ids": [fake_tag_id]}, cookies=cookies)
            logger.info(f"[TEST] Unassign from non-existent conversation status: {resp3.status_code}")
            assert resp3.status_code in [404, 400]  # Should fail
            
            logger.info("[TEST] All error cases handled correctly")
            
    except AssertionError as e:
        logger.error(f"[TEST] test_tag_error_handling failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_tag_error_handling unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_tag_error_handling completed successfully.")
