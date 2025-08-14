"""
Test session invalidation functionality.
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.services.auth.utils.session_auth import (
    create_session_token, 
    verify_session_token, 
    invalidate_session_token
)
from app.core.config import settings

client = TestClient(app)

class TestSessionInvalidation:
    """Test session invalidation functionality."""
    
    def test_session_invalidation(self):
        """Test that invalidated sessions cannot be reused."""
        # Create a test user
        user_data = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Create a session token
        token = create_session_token(user_data)
        assert token is not None
        
        # Verify the token is valid
        session_data = verify_session_token(token)
        assert session_data is not None
        assert session_data.email == "testuser@example.com"
        
        # Invalidate the token
        invalidate_session_token(token)
        
        # Verify the token is now invalid
        session_data = verify_session_token(token)
        assert session_data is None
    
    def test_logout_invalidates_session(self):
        """Test that logout endpoint invalidates the session token."""
        # First, create a user and login
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        # Login to get a session
        login_response = client.post("/api/v1/auth/users/login", json=login_data)
        assert login_response.status_code == 200
        
        # Get the session cookie
        cookies = login_response.cookies
        session_cookie = cookies.get("session_token")
        assert session_cookie is not None
        
        # Verify we can access a protected endpoint
        protected_response = client.get(
            "/api/v1/auth/users/me",
            cookies={"session_token": session_cookie}
        )
        assert protected_response.status_code == 200
        
        # Logout
        logout_response = client.post(
            "/api/v1/auth/users/logout",
            cookies={"session_token": session_cookie}
        )
        assert logout_response.status_code == 200
        
        # Verify the session cookie is cleared
        logout_cookies = logout_response.cookies
        cleared_cookie = logout_cookies.get("session_token")
        assert cleared_cookie is None or cleared_cookie.value == ""
        
        # Verify we cannot access protected endpoints with the old session
        protected_response_after_logout = client.get(
            "/api/v1/auth/users/me",
            cookies={"session_token": session_cookie}
        )
        assert protected_response_after_logout.status_code == 401
    
    def test_multiple_session_invalidation(self):
        """Test that multiple sessions can be invalidated."""
        user_data = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "testuser@example.com"
        }
        
        # Create multiple tokens
        token1 = create_session_token(user_data)
        token2 = create_session_token(user_data)
        token3 = create_session_token(user_data)
        
        # Verify all tokens are valid
        assert verify_session_token(token1) is not None
        assert verify_session_token(token2) is not None
        assert verify_session_token(token3) is not None
        
        # Invalidate tokens
        invalidate_session_token(token1)
        invalidate_session_token(token3)
        
        # Verify invalidated tokens are invalid
        assert verify_session_token(token1) is None
        assert verify_session_token(token3) is None
        
        # Verify non-invalidated token is still valid
        assert verify_session_token(token2) is not None
    
    def test_session_invalidation_cleanup(self):
        """Test that session invalidation cleanup works."""
        user_data = {
            "_id": "507f1f77bcf86cd799439011",
            "email": "testuser@example.com"
        }
        
        # Create many tokens to test cleanup
        tokens = []
        for i in range(1005):  # More than the cleanup threshold
            token = create_session_token(user_data)
            tokens.append(token)
        
        # Invalidate all tokens
        for token in tokens:
            invalidate_session_token(token)
        
        # Verify all tokens are invalid
        for token in tokens:
            assert verify_session_token(token) is None
