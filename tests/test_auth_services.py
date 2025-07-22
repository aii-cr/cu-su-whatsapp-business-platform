"""Tests for the new modular auth services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from httpx import AsyncClient
from app.core.config import settings

# Test the new auth services
from app.services.auth import (
    hash_password, verify_password, create_access_token, 
    create_refresh_token, verify_token, check_user_permission, get_user_roles, get_user_permissions
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

class TestTokenUtils:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        data = {"sub": "user_id_123"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        data = {"sub": "user_id_123"}
        token = create_refresh_token(data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        data = {"sub": "user_id_123"}
        token = create_access_token(data)
        payload = verify_token(token, "access")
        assert payload is not None
        assert payload["sub"] == "user_id_123"
        assert payload["type"] == "access"

# --- INTEGRATION TESTS ---

@pytest.fixture(scope="module")
async def login_token():
    """Fixture to log in and return a valid access token and user info."""
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        login_payload = {"email": "testuser@example.com", "password": "testpassword123"}
        resp = await ac.post(f"{settings.API_PREFIX}/auth/users/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()
        return data["access_token"], data["user"]

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(login_token):
    token, _ = login_token
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        # Access protected endpoint with valid token
        headers = {"Authorization": f"Bearer {token}"}
        resp = await ac.get(f"{settings.API_PREFIX}/users/me", headers=headers)
        assert resp.status_code == 200
        # Access protected endpoint with invalid token
        bad_headers = {"Authorization": "Bearer invalidtoken"}
        resp2 = await ac.get(f"{settings.API_PREFIX}/users/me", headers=bad_headers)
        assert resp2.status_code == 401
        # Access protected endpoint with no token
        resp3 = await ac.get(f"{settings.API_PREFIX}/users/me")
        assert resp3.status_code == 401

@pytest.mark.asyncio
async def test_user_permissions_and_roles(login_token):
    token, user = login_token
    user_id = user["id"] if "id" in user else user["_id"]
    # Permissions
    perms = await get_user_permissions(user_id)
    assert isinstance(perms, list)
    # Should have at least one permission (e.g., users:read or messages:send)
    assert any(p.startswith("users:") or p.startswith("messages:") for p in perms)
    # Roles
    roles = await get_user_roles(user_id)
    assert isinstance(roles, list)
    assert any("name" in r for r in roles)

@pytest.mark.asyncio
async def test_check_user_permission_positive_negative(login_token):
    token, user = login_token
    user_id = user["id"] if "id" in user else user["_id"]
    # Should have at least one permission
    perms = await get_user_permissions(user_id)
    if perms:
        # Test positive
        result = await check_user_permission(user_id, perms[0])
        assert result is True
    # Test negative (random permission)
    result2 = await check_user_permission(user_id, "not_a_real_permission")
    assert result2 is False

# --- END-TO-END AUTH FLOW ---

@pytest.mark.asyncio
async def test_access_with_expired_or_invalid_token():
    async with AsyncClient(base_url=settings.DOMAIN) as ac:
        # Use a clearly invalid token
        headers = {"Authorization": "Bearer invalidtoken"}
        resp = await ac.get(f"{settings.API_PREFIX}/users/me", headers=headers)
        assert resp.status_code == 401

# TODO: Add more tests for require_permissions, require_roles, and edge cases as needed 