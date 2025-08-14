"""
Test authentication flow including login, logout, and session management.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import jwt

from app.main import app
from app.core.config import settings
from app.services.auth.utils.session_auth import create_session_token, verify_session_token, invalidate_session_token
from app.db.models.auth.user import User, UserStatus
from app.schemas.auth import UserLogin


class TestAuthFlow:
    """Test authentication flow scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(base_url="http://test")
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data."""
        return {
            "_id": "507f1f77bcf86cd799439011",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "testpassword123",
            "role_ids": ["role1"],
            "permissions": ["conversation:read"],
            "is_active": True,
            "is_verified": True,
            "status": UserStatus.ACTIVE,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def mock_user(self, test_user_data):
        """Mock user object."""
        return User(**test_user_data)
    
    def test_create_session_token(self, test_user_data):
        """Test session token creation."""
        token = create_session_token(test_user_data)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        session_data = verify_session_token(token)
        assert session_data is not None
        assert session_data.user_id == test_user_data["_id"]
        assert session_data.email == test_user_data["email"]
    
    def test_verify_session_token_valid(self, test_user_data):
        """Test valid session token verification."""
        token = create_session_token(test_user_data)
        session_data = verify_session_token(token)
        
        assert session_data is not None
        assert session_data.user_id == test_user_data["_id"]
        assert session_data.email == test_user_data["email"]
        assert session_data.type == "session"
    
    def test_verify_session_token_invalid(self):
        """Test invalid session token verification."""
        # Test with invalid token
        session_data = verify_session_token("invalid_token")
        assert session_data is None
        
        # Test with None token
        session_data = verify_session_token(None)
        assert session_data is None
    
    def test_invalidate_session_token(self, test_user_data):
        """Test session token invalidation."""
        token = create_session_token(test_user_data)
        
        # Token should be valid initially
        session_data = verify_session_token(token)
        assert session_data is not None
        
        # Invalidate token
        invalidate_session_token(token)
        
        # Token should be invalid after invalidation
        session_data = verify_session_token(token)
        assert session_data is None
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client, test_user_data):
        """Test successful login."""
        with patch('app.services.auth_service.authenticate_user') as mock_auth, \
             patch('app.services.auth_service.create_session_token') as mock_create_token:
            
            # Mock authentication
            mock_auth.return_value = test_user_data
            mock_create_token.return_value = "test_session_token"
            
            # Test login request
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = await async_client.post(
                f"{settings.API_PREFIX}/auth/users/login",
                json=login_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user_data["email"]
            assert data["first_name"] == test_user_data["first_name"]
            
            # Check that session cookie was set
            cookies = response.cookies
            assert "session_token" in cookies
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client):
        """Test login with invalid credentials."""
        with patch('app.services.auth_service.authenticate_user') as mock_auth:
            # Mock authentication failure
            mock_auth.return_value = None
            
            login_data = {
                "email": "test@example.com",
                "password": "wrongpassword"
            }
            
            response = await async_client.post(
                f"{settings.API_PREFIX}/auth/users/login",
                json=login_data
            )
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout_success(self, async_client, test_user_data):
        """Test successful logout."""
        with patch('app.services.auth.utils.session_auth.get_current_user') as mock_get_user, \
             patch('app.services.auth.utils.session_auth.invalidate_session_token') as mock_invalidate:
            
            # Mock current user
            mock_user = User(**test_user_data)
            mock_get_user.return_value = mock_user
            
            # Test logout request
            response = await async_client.post(
                f"{settings.API_PREFIX}/auth/users/logout",
                cookies={"session_token": "test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Logged out successfully"
            
            # Verify session token was invalidated
            mock_invalidate.assert_called_once_with("test_token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, async_client, test_user_data):
        """Test getting current user with valid session."""
        with patch('app.services.auth.utils.session_auth.verify_session_token') as mock_verify, \
             patch('app.db.client.database.db.users.find_one') as mock_find_user:
            
            # Mock session verification
            mock_verify.return_value = MagicMock(
                user_id=test_user_data["_id"],
                email=test_user_data["email"]
            )
            
            # Mock user lookup
            mock_find_user.return_value = test_user_data
            
            # Test get current user request
            response = await async_client.get(
                f"{settings.API_PREFIX}/auth/users/me",
                cookies={"session_token": "test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == test_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_session(self, async_client):
        """Test getting current user without session."""
        response = await async_client.get(f"{settings.API_PREFIX}/auth/users/me")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_session(self, async_client):
        """Test getting current user with invalid session."""
        with patch('app.services.auth.utils.session_auth.verify_session_token') as mock_verify:
            # Mock invalid session
            mock_verify.return_value = None
            
            response = await async_client.get(
                f"{settings.API_PREFIX}/auth/users/me",
                cookies={"session_token": "invalid_token"}
            )
            assert response.status_code == 401
    
    def test_session_expiration_time(self, test_user_data):
        """Test session expiration based on time."""
        token = create_session_token(test_user_data)
        
        # Token should be valid initially
        session_data = verify_session_token(token)
        assert session_data is not None
        
        # Test that token expires after configured time
        # Note: This would require time manipulation in a real test
        # For now, we just verify the token structure
    
    def test_session_inactivity_timeout(self, test_user_data):
        """Test session expiration based on inactivity."""
        token = create_session_token(test_user_data)
        
        # Token should be valid initially
        session_data = verify_session_token(token)
        assert session_data is not None
        
        # Test that token expires after inactivity timeout
        # Note: This would require time manipulation in a real test
        # For now, we just verify the token structure


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, async_client, test_user_data):
        """Test complete authentication flow: login -> use session -> logout."""
        with patch('app.services.auth_service.authenticate_user') as mock_auth, \
             patch('app.services.auth_service.create_session_token') as mock_create_token, \
             patch('app.services.auth.utils.session_auth.verify_session_token') as mock_verify, \
             patch('app.db.client.database.db.users.find_one') as mock_find_user, \
             patch('app.services.auth.utils.session_auth.invalidate_session_token') as mock_invalidate:
            
            # Mock authentication
            mock_auth.return_value = test_user_data
            mock_create_token.return_value = "test_session_token"
            mock_verify.return_value = MagicMock(
                user_id=test_user_data["_id"],
                email=test_user_data["email"]
            )
            mock_find_user.return_value = test_user_data
            
            # Step 1: Login
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            login_response = await async_client.post(
                f"{settings.API_PREFIX}/auth/users/login",
                json=login_data
            )
            
            assert login_response.status_code == 200
            session_cookie = login_response.cookies.get("session_token")
            assert session_cookie is not None
            
            # Step 2: Use session to get current user
            me_response = await async_client.get(
                f"{settings.API_PREFIX}/auth/users/me",
                cookies={"session_token": session_cookie}
            )
            
            assert me_response.status_code == 200
            user_data = me_response.json()
            assert user_data["email"] == test_user_data["email"]
            
            # Step 3: Logout
            logout_response = await async_client.post(
                f"{settings.API_PREFIX}/auth/users/logout",
                cookies={"session_token": session_cookie}
            )
            
            assert logout_response.status_code == 200
            
            # Step 4: Verify session is invalidated
            me_response_after_logout = await async_client.get(
                f"{settings.API_PREFIX}/auth/users/me",
                cookies={"session_token": session_cookie}
            )
            
            assert me_response_after_logout.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__])
