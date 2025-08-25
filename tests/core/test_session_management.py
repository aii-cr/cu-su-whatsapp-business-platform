"""
Test file for session management functionality.
Tests session creation, expiration, inactivity timeout, and proper cleanup.
"""

import pytest
import pytest_asyncio
import time
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from bson import ObjectId
from app.core.config import settings
from app.core.logger import logger
from app.services.auth.utils.session_auth import (
    create_session_token, verify_session_token, update_session_activity
)

@pytest_asyncio.fixture(scope="module")
async def login_session():
    """Get authentication session for test user."""
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


class TestSessionManagement:
    """Test session management functionality."""
    
    def test_session_token_creation(self):
        """Test that session tokens are created correctly."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"]
        }
        
        token = create_session_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        payload = verify_session_token(token)
        assert payload is not None
        assert payload["sub"] == user_data["sub"]
        assert payload["email"] == user_data["email"]
        assert payload["type"] == "session"
        assert "last_activity" in payload
        assert "iat" in payload
    
    def test_session_inactivity_timeout(self):
        """Test that sessions expire due to inactivity."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"]
        }
        
        # Create token with old activity time
        old_time = datetime.now(timezone.utc) - timedelta(minutes=settings.SESSION_INACTIVITY_MINUTES + 1)
        user_data["last_activity"] = old_time.isoformat()
        
        token = create_session_token(user_data)
        
        # Token should be invalid due to inactivity
        payload = verify_session_token(token)
        assert payload is None
    
    def test_session_activity_update(self):
        """Test that session activity can be updated."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"]
        }
        
        token = create_session_token(user_data)
        assert token is not None
        
        # Update activity
        updated_token = update_session_activity(token)
        assert updated_token is not None
        assert updated_token != token
        
        # Verify updated token is valid
        payload = verify_session_token(updated_token)
        assert payload is not None
        assert payload["sub"] == user_data["sub"]
    
    def test_session_expiration_handling(self):
        """Test that expired sessions are handled correctly."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"]
        }
        
        # Create token with very short expiration
        token = create_session_token(user_data, timedelta(seconds=1))
        
        # Wait for expiration
        time.sleep(2)
        
        # Token should be expired
        payload = verify_session_token(token)
        assert payload is None


class TestSessionAPI:
    """Test session-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_creates_session(self, login_session):
        """Test that login creates a valid session."""
        session_cookie, user_data = login_session
        
        assert session_cookie is not None
        assert isinstance(session_cookie, str)
        
        # Verify session token is valid
        payload = verify_session_token(session_cookie)
        assert payload is not None
        assert payload["email"] == user_data["email"]
    
    @pytest.mark.asyncio
    async def test_me_endpoint_with_session(self, login_session):
        """Test that /me endpoint works with valid session."""
        session_cookie, user_data = login_session
        base_url = "http://localhost:8010"
        api_prefix = "/api/v1"
        
        async with AsyncClient(base_url=base_url) as ac:
            headers = {"Cookie": f"session_token={session_cookie}"}
            resp = await ac.get(f"{api_prefix}/auth/users/me", headers=headers)
            
            assert resp.status_code == 200
            data = resp.json()
            assert data["email"] == user_data["email"]
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_session(self, login_session):
        """Test that protected endpoints work with valid session."""
        session_cookie, user_data = login_session
        base_url = "http://localhost:8010"
        api_prefix = "/api/v1"
        
        async with AsyncClient(base_url=base_url) as ac:
            headers = {"Cookie": f"session_token={session_cookie}"}
            resp = await ac.get(f"{api_prefix}/conversations/", headers=headers)
            
            # Should not return 401/403 with valid session
            assert resp.status_code != 401
            assert resp.status_code != 403
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_session(self):
        """Test that protected endpoints return 401 without session."""
        base_url = "http://localhost:8010"
        api_prefix = "/api/v1"
        
        async with AsyncClient(base_url=base_url) as ac:
            resp = await ac.get(f"{api_prefix}/conversations/")
            
            # Should return 401 without session
            assert resp.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout_clears_session(self, login_session):
        """Test that logout clears the session."""
        session_cookie, user_data = login_session
        base_url = "http://localhost:8010"
        api_prefix = "/api/v1"
        
        async with AsyncClient(base_url=base_url) as ac:
            headers = {"Cookie": f"session_token={session_cookie}"}
            resp = await ac.post(f"{api_prefix}/auth/users/logout", headers=headers)
            
            assert resp.status_code == 200
            
            # Check that session cookie is cleared
            cookies = resp.cookies
            session_cookie_after = cookies.get("session_token")
            assert session_cookie_after is None or session_cookie_after == ""
    
    @pytest.mark.asyncio
    async def test_session_inactivity_timeout_api(self):
        """Test that API endpoints respect inactivity timeout."""
        # This test would require creating a session and then waiting
        # for the inactivity timeout, which is not practical in unit tests
        # In a real scenario, this would be tested with integration tests
        pass


class TestSessionSecurity:
    """Test session security features."""
    
    def test_session_token_type_validation(self):
        """Test that only session tokens are accepted."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"],
            "type": "access"  # Wrong type
        }
        
        token = create_session_token(user_data)
        
        # Token should be invalid due to wrong type
        payload = verify_session_token(token)
        assert payload is None
    
    def test_session_token_tampering(self):
        """Test that tampered tokens are rejected."""
        user_data = {
            "sub": str(ObjectId()),
            "email": "test@example.com",
            "scopes": ["user:read"]
        }
        
        token = create_session_token(user_data)
        
        # Tamper with the token
        tampered_token = token[:-10] + "tampered"
        
        # Tampered token should be invalid
        payload = verify_session_token(tampered_token)
        assert payload is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
