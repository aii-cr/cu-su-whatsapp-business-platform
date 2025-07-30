import asyncio
from app.db.client import database
from app.services.auth import hash_password
from datetime import datetime, timezone
from bson import ObjectId

async def insert_normal_test_user():
    await database.connect()

    # Ensure permission exists
    permission_key = "users:read"
    permission = await database.db.permissions.find_one({"key": permission_key})
    if not permission:
        perm_result = await database.db.permissions.insert_one({
            "key": permission_key,
            "name": "Read Users",
            "is_active": True
        })
        permission_id = perm_result.inserted_id
    else:
        permission_id = permission["_id"]

    # Ensure role exists
    role_name = "TestRole"
    role = await database.db.roles.find_one({"name": role_name})
    if not role:
        role_result = await database.db.roles.insert_one({
            "name": role_name,
            "permission_ids": [permission_id],
            "is_active": True
        })
        role_id = role_result.inserted_id
    else:
        role_id = role["_id"]
        # Ensure permission is in the role
        if permission_id not in role.get("permission_ids", []):
            await database.db.roles.update_one(
                {"_id": role_id},
                {"$addToSet": {"permission_ids": permission_id}}
            )

    # Remove existing user if present
    await database.db.users.delete_many({"email": "pytestuser@example.com"})

    # Insert non-superadmin user with the role
    user_doc = {
        "name": "Pytest User",
        "first_name": "Pytest",
        "last_name": "User",
        "email": "pytestuser@example.com",
        "phone_number": "+1234567899",
        "password_hash": hash_password("pytestpassword123"),
        "role_ids": [role_id],
        "department_id": None,
        "is_super_admin": False,
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
    print(f"Inserted pytest user with _id: {result.inserted_id}")
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(insert_normal_test_user()) 