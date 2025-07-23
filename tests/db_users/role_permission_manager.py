import asyncio
from app.db.client import database
from bson import ObjectId

async def add_role(role_name, permission_keys=None):
    await database.connect()
    permission_keys = permission_keys or []
    # Check if role exists
    role = await database.db.roles.find_one({"name": role_name})
    if role:
        print(f"Role '{role_name}' already exists (id: {role['_id']})")
        await database.disconnect()
        return role['_id']
    # Get permission ObjectIds
    permission_ids = []
    for key in permission_keys:
        perm = await database.db.permissions.find_one({"key": key})
        if not perm:
            perm_result = await database.db.permissions.insert_one({
                "key": key,
                "name": key.replace(":", " ").title(),
                "is_active": True
            })
            permission_ids.append(perm_result.inserted_id)
        else:
            permission_ids.append(perm["_id"])
    # Insert role
    result = await database.db.roles.insert_one({
        "name": role_name,
        "permission_ids": permission_ids,
        "is_active": True
    })
    print(f"Created role '{role_name}' with id: {result.inserted_id}")
    await database.disconnect()
    return result.inserted_id

async def append_permissions_to_role(role_name, permission_keys):
    await database.connect()
    role = await database.db.roles.find_one({"name": role_name})
    if not role:
        print(f"Role '{role_name}' does not exist.")
        await database.disconnect()
        return
    # Get permission ObjectIds
    permission_ids = []
    for key in permission_keys:
        perm = await database.db.permissions.find_one({"key": key})
        if not perm:
            perm_result = await database.db.permissions.insert_one({
                "key": key,
                "name": key.replace(":", " ").title(),
                "is_active": True
            })
            permission_ids.append(perm_result.inserted_id)
        else:
            permission_ids.append(perm["_id"])
    # Check for duplicates
    already_has = [pid for pid in permission_ids if pid in role.get("permission_ids", [])]
    new_ids = [pid for pid in permission_ids if pid not in role.get("permission_ids", [])]
    if not new_ids:
        print(f"Role '{role_name}' already has all these permissions.")
    else:
        await database.db.roles.update_one(
            {"_id": role["_id"]},
            {"$addToSet": {"permission_ids": {"$each": new_ids}}}
        )
        print(f"Appended permissions to role '{role_name}': {[str(pid) for pid in new_ids]}")
    await database.disconnect()

async def delete_role(role_name):
    await database.connect()
    result = await database.db.roles.delete_one({"name": role_name})
    if result.deleted_count:
        print(f"Deleted role '{role_name}'")
    else:
        print(f"Role '{role_name}' not found.")
    await database.disconnect()

async def delete_permission(permission_key):
    await database.connect()
    result = await database.db.permissions.delete_one({"key": permission_key})
    if result.deleted_count:
        print(f"Deleted permission '{permission_key}'")
    else:
        print(f"Permission '{permission_key}' not found.")
    await database.disconnect()

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(description="Role/Permission Manager")
    subparsers = parser.add_subparsers(dest="command")

    add_role_parser = subparsers.add_parser("add-role")
    add_role_parser.add_argument("role_name")
    add_role_parser.add_argument("--permissions", nargs="*", default=[])

    append_perm_parser = subparsers.add_parser("append-perms")
    append_perm_parser.add_argument("role_name")
    append_perm_parser.add_argument("permissions", nargs="+")

    del_role_parser = subparsers.add_parser("delete-role")
    del_role_parser.add_argument("role_name")

    del_perm_parser = subparsers.add_parser("delete-perm")
    del_perm_parser.add_argument("permission_key")

    args = parser.parse_args()
    if args.command == "add-role":
        asyncio.run(add_role(args.role_name, args.permissions))
    elif args.command == "append-perms":
        asyncio.run(append_permissions_to_role(args.role_name, args.permissions))
    elif args.command == "delete-role":
        asyncio.run(delete_role(args.role_name))
    elif args.command == "delete-perm":
        asyncio.run(delete_permission(args.permission_key))
    else:
        parser.print_help() 