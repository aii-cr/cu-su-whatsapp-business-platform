"""
Test cases for conversation claiming functionality.
"""

import pytest
from httpx import AsyncClient
from bson import ObjectId
from datetime import datetime, timezone

from app.main import app
from app.db.client import database
from app.services.auth.utils.session_auth import create_access_token


@pytest.fixture
async def test_user():
    """Create a test user for authentication."""
    db = await database._get_db()
    
    # Create test user
    user_data = {
        "_id": ObjectId(),
        "email": "testagent@example.com",
        "name": "Test Agent",
        "password_hash": "hashed_password",
        "is_active": True,
        "is_super_admin": False,
        "role_ids": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_data)
    
    # Create access token
    token = create_access_token(data={"sub": str(user_data["_id"])})
    
    yield {
        "user": user_data,
        "token": token
    }
    
    # Cleanup
    await db.users.delete_one({"_id": user_data["_id"]})


@pytest.fixture
async def test_conversation():
    """Create a test conversation."""
    db = await database._get_db()
    
    conversation_data = {
        "_id": ObjectId(),
        "customer_phone": "1234567890",
        "customer_name": "Test Customer",
        "status": "pending",
        "priority": "normal",
        "channel": "whatsapp",
        "assigned_agent_id": None,  # Unassigned
        "message_count": 0,
        "unread_count": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.conversations.insert_one(conversation_data)
    
    yield conversation_data
    
    # Cleanup
    await db.conversations.delete_one({"_id": conversation_data["_id"]})


@pytest.mark.asyncio
async def test_claim_conversation_success(test_user, test_conversation):
    """Test successful conversation claiming."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = await ac.post(
            f"/api/v1/conversations/{test_conversation['_id']}/claim",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that conversation is now assigned
        assert data["assigned_agent_id"] == str(test_user["user"]["_id"])
        assert data["status"] == "active"
        
        # Verify in database
        db = await database._get_db()
        updated_conversation = await db.conversations.find_one({"_id": test_conversation["_id"]})
        assert updated_conversation["assigned_agent_id"] == test_user["user"]["_id"]
        assert updated_conversation["status"] == "active"


@pytest.mark.asyncio
async def test_claim_already_assigned_conversation(test_user, test_conversation):
    """Test claiming a conversation that's already assigned."""
    db = await database._get_db()
    
    # First, assign the conversation to another user
    other_user_id = ObjectId()
    await db.conversations.update_one(
        {"_id": test_conversation["_id"]},
        {"$set": {"assigned_agent_id": other_user_id, "status": "active"}}
    )
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = await ac.post(
            f"/api/v1/conversations/{test_conversation['_id']}/claim",
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already assigned" in data["detail"].lower()


@pytest.mark.asyncio
async def test_claim_nonexistent_conversation(test_user):
    """Test claiming a conversation that doesn't exist."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        fake_conversation_id = str(ObjectId())
        response = await ac.post(
            f"/api/v1/conversations/{fake_conversation_id}/claim",
            headers=headers
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_claim_conversation_unauthorized():
    """Test claiming conversation without authentication."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        fake_conversation_id = str(ObjectId())
        response = await ac.post(f"/api/v1/conversations/{fake_conversation_id}/claim")
        
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auto_assign_on_first_message(test_user, test_conversation):
    """Test auto-assignment when agent sends first message."""
    db = await database._get_db()
    
    # Send a message as an agent to an unassigned conversation
    message_data = {
        "conversation_id": test_conversation["_id"],
        "type": "text",
        "direction": "outbound",
        "sender_role": "agent",
        "sender_id": test_user["user"]["_id"],
        "sender_name": test_user["user"]["name"],
        "text_content": "Hello, I'm here to help!",
        "status": "sent",
        "timestamp": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    await db.messages.insert_one(message_data)
    
    # Check that conversation was auto-assigned
    updated_conversation = await db.conversations.find_one({"_id": test_conversation["_id"]})
    assert updated_conversation["assigned_agent_id"] == test_user["user"]["_id"]
    assert updated_conversation["status"] == "active"
    
    # Cleanup
    await db.messages.delete_one({"conversation_id": test_conversation["_id"]})
