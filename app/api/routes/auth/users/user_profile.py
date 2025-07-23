"""User profile management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from app.services.auth import get_current_active_user
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.schemas.auth import UserProfileResponse

router = APIRouter()

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user = Depends(get_current_active_user)):
    """
    Get current user's profile with permissions and roles.
    """
    db = database.db
    # Get user with populated role and department info
    user_data = await db.users.aggregate([
        {"$match": {"_id": current_user.id}},
        {"$lookup": {
            "from": "departments",
            "localField": "department_id",
            "foreignField": "_id",
            "as": "department"
        }},
        {"$lookup": {
            "from": "roles",
            "localField": "role_ids",
            "foreignField": "_id",
            "as": "roles"
        }}
    ]).to_list(1)
    if not user_data:
        raise HTTPException(
            status_code=404,
            detail=ErrorCode.USER_NOT_FOUND
        )
    user = user_data[0]
    # Get permissions from roles
    permissions = []
    role_names = []
    for role in user.get("roles", []):
        role_names.append(role["name"])
        # Get permissions for this role
        role_permissions = await db.permissions.find(
            {"_id": {"$in": role.get("permission_ids", [])}}
        ).to_list(None)
        permissions.extend([p["key"] for p in role_permissions])
    # Create response
    profile = UserProfileResponse(**user)
    profile.permissions = list(set(permissions))  # Remove duplicates
    profile.role_names = role_names
    profile.department_name = user.get("department", [{}])[0].get("name") if user.get("department") else None
    return profile 