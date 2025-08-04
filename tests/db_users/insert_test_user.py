import asyncio
from app.services.auth import hash_password
from datetime import datetime, timezone

async def insert_test_user():
    await database.connect()
    user_doc = {
        "name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com",
        "phone_number": "+1234567890",
        "password_hash": hash_password("testpassword123"),
        "role_ids": [],
        "department_id": None,
        "is_super_admin": True,
        "avatar_url": None,
        "bio": None,
        "timezone": "UTC",
        "language": "en",
        "status": "active",
        "is_active": True,
        "is_online": False,
        "last_seen": None,
        "last_login": None,
        "max_concurrent_chats": 5,
        "auto_assignment_enabled": True,
        "notification_preferences": {
            "email_notifications": True,
            "push_notifications": True,
            "sound_notifications": True,
            "desktop_notifications": True
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": None,
        "updated_by": None,
        "total_conversations": 0,
        "average_response_time": None,
        "customer_satisfaction_rating": None,
    }
    # Remove None fields for MongoDB
    user_doc = {k: v for k, v in user_doc.items() if v is not None}
    result = await database.db.users.insert_one(user_doc)
    print(f"Inserted user with _id: {result.inserted_id}")
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(insert_test_user())
