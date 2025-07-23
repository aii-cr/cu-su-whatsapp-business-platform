import asyncio
from app.db.client import database
from bson import ObjectId

async def add_role_to_user(user_email, role_name):
    await database.connect()
    user = await database.db.users.find_one({"email": user_email})
    if not user:
        print(f"User with email '{user_email}' not found.")
        await database.disconnect()
        return
    role = await database.db.roles.find_one({"name": role_name})
    if not role:
        print(f"Role '{role_name}' not found.")
        await database.disconnect()
        return
    role_id = role["_id"]
    if role_id in user.get("role_ids", []):
        print(f"User '{user_email}' already has role '{role_name}'.")
    else:
        await database.db.users.update_one(
            {"_id": user["_id"]},
            {"$addToSet": {"role_ids": role_id}}
        )
        print(f"Added role '{role_name}' to user '{user_email}'.")
    await database.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Add a role to a user by email.")
    parser.add_argument("user_email", help="User's email address")
    parser.add_argument("role_name", help="Role name to add")
    args = parser.parse_args()
    asyncio.run(add_role_to_user(args.user_email, args.role_name)) 