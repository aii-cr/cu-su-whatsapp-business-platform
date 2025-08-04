"""Tests for the new modular auth services."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from httpx import AsyncClient
from app.core.config import settings

# Test the new auth services
from app.services.auth import (
    hash_password, verify_password, create_session_token, 
    verify_session_token, check_user_permission, get_user_roles, get_user_permissions
)

# --- UNIT TESTS ---

class TestPasswordUtils:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2b$")
    
    def test_verify_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

class TestSessionUtils:
    """Test session token creation and verification."""
    
    def test_create_session_token(self):
        data = {"sub": "user_id_123"}
        token = create_session_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_session_token(self):
        data = {"sub": "user_id_123"}
        token = create_session_token(data)
        payload = verify_session_token(token)
        assert payload is not None
        assert payload["sub"] == "user_id_123"
        assert payload["type"] == "session"

# --- INTEGRATION TESTS ---

@pytest_asyncio.fixture(scope="module")
async def login_session():
    """Fixture to log in and return session cookie and user info."""
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        login_payload = {"email": "pytestuser@example.com", "password": "pytestpassword123"}
        resp = await ac.post(f"{settings.API_PREFIX}/auth/users/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()
        # Get session cookie from response
        cookies = resp.cookies
        session_cookie = cookies.get("session_token")
        return session_cookie, data

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(login_session):
    session_cookie, _ = login_session
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        # Access protected endpoint with valid session
        cookies = {"session_token": session_cookie}
        resp = await ac.get(f"{settings.API_PREFIX}/auth/users/me", cookies=cookies)
        assert resp.status_code == 200
        # Access protected endpoint with invalid session
        bad_cookies = {"session_token": "invalidtoken"}
        resp2 = await ac.get(f"{settings.API_PREFIX}/auth/users/me", cookies=bad_cookies)
        assert resp2.status_code in (401, 403)  # Accept 401 or 403
        # Access protected endpoint with no session
        resp3 = await ac.get(f"{settings.API_PREFIX}/auth/users/me")
        assert resp3.status_code in (401, 403)

@pytest.mark.asyncio
async def test_user_permissions_and_roles(login_session):
    session_cookie, user = login_session
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        cookies = {"session_token": session_cookie}
        resp = await ac.get(f"{settings.API_PREFIX}/auth/users/me", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        perms = data.get("permissions", [])
        roles = data.get("role_names", [])
        assert isinstance(perms, list)
        assert any(p.startswith("users:") or p.startswith("messages:") for p in perms)
        assert isinstance(roles, list)
        assert len(roles) > 0

@pytest.mark.asyncio
async def test_check_user_permission_positive_negative(login_session):
    session_cookie, user = login_session
    user_id = user["id"] if "id" in user else user["_id"]
    from app.services.auth import get_user_permissions, check_user_permission
    perms = await get_user_permissions(user_id)
    if perms:
        result = await check_user_permission(user_id, perms[0])
        assert result is True
    result2 = await check_user_permission(user_id, "not_a_real_permission")
    assert result2 is False

# --- END-TO-END AUTH FLOW ---

@pytest.mark.asyncio
async def test_access_with_expired_or_invalid_session():
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        # Use a clearly invalid session token
        cookies = {"session_token": "invalidtoken"}
        resp = await ac.get(f"{settings.API_PREFIX}/auth/users/me", cookies=cookies)
        assert resp.status_code in (401, 403)

# TODO: Add more tests for require_permissions, require_roles, and edge cases as needed 