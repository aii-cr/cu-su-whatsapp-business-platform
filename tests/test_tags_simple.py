"""
Simple and comprehensive tests for Tags API endpoints.
Tests all tag functionality with proper authentication.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.core.config import settings
from app.core.logger import logger


# Test configuration
BASE_URL = "http://localhost:8010"
API_PREFIX = "/api/v1"

# Test user credentials
TEST_USER = {
    "email": "testuser@example.com", 
    "password": "testpassword123"
}


async def create_authenticated_client():
    """Create an authenticated HTTP client."""
    client = AsyncClient(base_url=BASE_URL)
    
    # Login to get authentication cookies
    login_resp = await client.post(f"{API_PREFIX}/auth/users/login", json=TEST_USER)
    
    if login_resp.status_code != 200:
        await client.aclose()
        raise Exception(f"Authentication failed: {login_resp.status_code} - {login_resp.text}")
    
    user = login_resp.json()
    logger.info(f"[TEST] Authenticated as {user['email']}")
    
    return client, user


class TestTagsAPI:
    """Test Tags API functionality."""
    
    @pytest.mark.asyncio
    async def test_create_tag(self):
        """Test creating a new tag."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag creation...")
            
            tag_data = {
                "name": "Test Tag Creation", 
                "color": "#f59e0b",
                "category": "general",
                "description": "A test tag for creation"
            }
            
            resp = await client.post(f"{API_PREFIX}/tags/", json=tag_data)
            
            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
            
            tag = resp.json()
            assert tag["name"] == tag_data["name"]
            assert tag["color"] == tag_data["color"]
            assert tag["category"] == tag_data["category"]
            assert tag["description"] == tag_data["description"]
            assert tag["slug"] == "test-tag-creation"
            assert tag["usage_count"] == 0
            assert tag["status"] == "active"
            assert "id" in tag
            assert "created_at" in tag
            
            logger.info(f"[TEST] ✅ Successfully created tag: {tag['name']} (ID: {tag['id']})")
            
            # Cleanup
            await client.delete(f"{API_PREFIX}/tags/{tag['id']}")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_list_tags(self):
        """Test listing tags with pagination."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag listing...")
            
            resp = await client.get(f"{API_PREFIX}/tags/", params={
                "limit": 10,
                "offset": 0,
                "sort_by": "name",
                "sort_order": "asc"
            })
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            
            data = resp.json()
            assert "tags" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "has_more" in data
            assert isinstance(data["tags"], list)
            
            logger.info(f"[TEST] ✅ Successfully listed {len(data['tags'])} tags (total: {data['total']})")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_suggest_tags_empty_query(self):
        """Test tag suggestions with empty query (popular tags)."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag suggestions (popular tags)...")
            
            resp = await client.get(f"{API_PREFIX}/tags/suggest", params={
                "q": "",
                "limit": 5
            })
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            
            data = resp.json()
            assert "suggestions" in data
            assert "total" in data
            assert isinstance(data["suggestions"], list)
            
            logger.info(f"[TEST] ✅ Got {len(data['suggestions'])} popular tag suggestions")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_suggest_tags_with_query(self):
        """Test tag suggestions with search query."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag suggestions with query...")
            
            resp = await client.get(f"{API_PREFIX}/tags/suggest", params={
                "q": "test",
                "limit": 5
            })
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            
            data = resp.json()
            assert "suggestions" in data
            assert "total" in data
            
            logger.info(f"[TEST] ✅ Got {len(data['suggestions'])} suggestions for 'test'")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_tag_settings(self):
        """Test getting tag settings."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag settings...")
            
            resp = await client.get(f"{API_PREFIX}/tags/settings")
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            
            data = resp.json()
            assert "max_tags_per_conversation" in data
            assert isinstance(data["max_tags_per_conversation"], int)
            assert data["max_tags_per_conversation"] > 0
            
            logger.info(f"[TEST] ✅ Tag settings: max_tags_per_conversation = {data['max_tags_per_conversation']}")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_search_tags(self):
        """Test tag search endpoint."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag search...")
            
            resp = await client.get(f"{API_PREFIX}/tags/search", params={
                "q": "test",
                "limit": 5
            })
            
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            
            data = resp.json()
            assert "tags" in data
            assert "total" in data
            
            logger.info(f"[TEST] ✅ Search found {len(data['tags'])} tags for 'test'")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio  
    async def test_full_tag_lifecycle(self):
        """Test complete tag lifecycle: create, read, update, delete."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing full tag lifecycle...")
            
            # 1. Create tag
            tag_data = {
                "name": "Lifecycle Test Tag",
                "color": "#0066cc", 
                "category": "general",
                "description": "Tag for lifecycle testing"
            }
            
            create_resp = await client.post(f"{API_PREFIX}/tags/", json=tag_data)
            assert create_resp.status_code == 201
            tag = create_resp.json()
            tag_id = tag["id"]
            
            logger.info(f"[TEST] ✅ Created tag: {tag['name']} (ID: {tag_id})")
            
            # 2. Read tag
            get_resp = await client.get(f"{API_PREFIX}/tags/{tag_id}")
            assert get_resp.status_code == 200
            retrieved_tag = get_resp.json()
            assert retrieved_tag["name"] == tag_data["name"]
            
            logger.info(f"[TEST] ✅ Retrieved tag: {retrieved_tag['name']}")
            
            # 3. Update tag
            update_data = {
                "name": "Updated Lifecycle Tag",
                "color": "#cc0066",
                "description": "Updated description"
            }
            
            update_resp = await client.put(f"{API_PREFIX}/tags/{tag_id}", json=update_data)
            assert update_resp.status_code == 200
            updated_tag = update_resp.json()
            assert updated_tag["name"] == update_data["name"]
            assert updated_tag["color"] == update_data["color"]
            
            logger.info(f"[TEST] ✅ Updated tag: {updated_tag['name']}")
            
            # 4. Delete tag (soft delete)
            delete_resp = await client.delete(f"{API_PREFIX}/tags/{tag_id}")
            assert delete_resp.status_code == 204
            
            # 5. Verify soft delete
            verify_resp = await client.get(f"{API_PREFIX}/tags/{tag_id}")
            assert verify_resp.status_code == 200
            deleted_tag = verify_resp.json()
            assert deleted_tag["status"] == "inactive"
            
            logger.info(f"[TEST] ✅ Soft deleted tag: {deleted_tag['name']}")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_tag_validation(self):
        """Test tag input validation."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing tag validation...")
            
            # Test missing required fields
            resp = await client.post(f"{API_PREFIX}/tags/", json={})
            assert resp.status_code == 422  # Validation error
            
            # Test invalid color format
            resp = await client.post(f"{API_PREFIX}/tags/", json={
                "name": "Test",
                "color": "invalid-color"
            })
            assert resp.status_code in [400, 422]  # Validation error (either is acceptable)
            
            # Test name too long
            resp = await client.post(f"{API_PREFIX}/tags/", json={
                "name": "x" * 100,  # Too long
                "color": "#ffffff"
            })
            assert resp.status_code in [400, 422]  # Validation error (either is acceptable)
            
            logger.info("[TEST] ✅ Tag validation working correctly")
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_nonexistent_resources(self):
        """Test handling of non-existent resources."""
        client, user = await create_authenticated_client()
        
        try:
            logger.info("[TEST] Testing non-existent resource handling...")
            
            fake_id = "65a1b2c3d4e5f6789abcdef0"
            
            # Test getting non-existent tag
            resp = await client.get(f"{API_PREFIX}/tags/{fake_id}")
            assert resp.status_code == 404
            
            # Test getting tags for non-existent conversation
            resp = await client.get(f"{API_PREFIX}/conversations/{fake_id}/tags")
            assert resp.status_code == 404
            
            logger.info("[TEST] ✅ Non-existent resource handling working correctly")
            
        finally:
            await client.aclose()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
