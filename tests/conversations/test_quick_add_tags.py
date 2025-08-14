"""
Test file for quick add tags functionality.
Tests the new quick add tags endpoint that returns most frequently used tags.
Uses the super admin user for authentication.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
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

@pytest.mark.asyncio
async def test_get_quick_add_tags(login_token):
    """Test quick add tags endpoint."""
    logger.info("[TEST] Starting test_get_quick_add_tags")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test default limit (7 tags)
            resp = await ac.get(f"{api_prefix}/tags/quick-add", cookies=cookies)
            logger.info(f"[TEST] Quick add tags status: {resp.status_code}")
            assert resp.status_code == 200
            data = resp.json()
            assert "suggestions" in data
            assert isinstance(data["suggestions"], list)
            assert len(data["suggestions"]) <= 7  # Default limit
            logger.info(f"[TEST] Quick add tags returned {len(data['suggestions'])} tags")
            
            # Verify tags have usage_count > 0
            for tag in data["suggestions"]:
                assert "usage_count" in tag
                assert tag["usage_count"] > 0
                assert "name" in tag
                assert "color" in tag
                assert "category" in tag
            
            # Test with custom limit
            resp2 = await ac.get(f"{api_prefix}/tags/quick-add?limit=5", cookies=cookies)
            logger.info(f"[TEST] Quick add tags with custom limit status: {resp2.status_code}")
            assert resp2.status_code == 200
            data2 = resp2.json()
            assert "suggestions" in data2
            assert isinstance(data2["suggestions"], list)
            assert len(data2["suggestions"]) <= 5  # Custom limit
            logger.info(f"[TEST] Quick add tags with custom limit returned {len(data2['suggestions'])} tags")
            
            # Test that tags are sorted by usage_count (descending)
            if len(data2["suggestions"]) > 1:
                usage_counts = [tag["usage_count"] for tag in data2["suggestions"]]
                assert usage_counts == sorted(usage_counts, reverse=True)
                logger.info("[TEST] Tags are correctly sorted by usage count (descending)")
                
    except AssertionError as e:
        logger.error(f"[TEST] test_get_quick_add_tags failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_get_quick_add_tags unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_get_quick_add_tags completed successfully.")

@pytest.mark.asyncio
async def test_quick_add_tags_unauthorized():
    """Test quick add tags endpoint without authentication."""
    logger.info("[TEST] Starting test_quick_add_tags_unauthorized")
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            # Test without authentication
            resp = await ac.get(f"{api_prefix}/tags/quick-add")
            logger.info(f"[TEST] Quick add tags unauthorized status: {resp.status_code}")
            assert resp.status_code in [401, 403]  # Unauthorized or Forbidden
            
    except AssertionError as e:
        logger.error(f"[TEST] test_quick_add_tags_unauthorized failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_quick_add_tags_unauthorized unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_quick_add_tags_unauthorized completed successfully.")

@pytest.mark.asyncio
async def test_quick_add_tags_limit_validation(login_token):
    """Test quick add tags endpoint with invalid limits."""
    logger.info("[TEST] Starting test_quick_add_tags_limit_validation")
    session_cookie, _ = login_token
    base_url = "http://localhost:8010"
    api_prefix = "/api/v1"
    
    try:
        async with AsyncClient(base_url=base_url) as ac:
            cookies = {"session_token": session_cookie}
            
            # Test with invalid limit (too high)
            resp = await ac.get(f"{api_prefix}/tags/quick-add?limit=100", cookies=cookies)
            logger.info(f"[TEST] Quick add tags with high limit status: {resp.status_code}")
            assert resp.status_code == 422  # Validation error
            
            # Test with invalid limit (negative)
            resp2 = await ac.get(f"{api_prefix}/tags/quick-add?limit=-1", cookies=cookies)
            logger.info(f"[TEST] Quick add tags with negative limit status: {resp2.status_code}")
            assert resp2.status_code == 422  # Validation error
            
            # Test with invalid limit (zero)
            resp3 = await ac.get(f"{api_prefix}/tags/quick-add?limit=0", cookies=cookies)
            logger.info(f"[TEST] Quick add tags with zero limit status: {resp3.status_code}")
            assert resp3.status_code == 422  # Validation error
            
    except AssertionError as e:
        logger.error(f"[TEST] test_quick_add_tags_limit_validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"[TEST] test_quick_add_tags_limit_validation unexpected error: {e}")
        raise
    
    logger.info("[TEST] test_quick_add_tags_limit_validation completed successfully.")
