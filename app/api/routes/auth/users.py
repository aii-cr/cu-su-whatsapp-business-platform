"""User management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from typing import List, Optional
from bson import ObjectId

from app.schemas.auth import (
    UserRegister, UserLogin, UserUpdate, PasswordChange, 
    PasswordResetRequest, PasswordResetConfirm, UserResponse, 
    UserListResponse, UserProfileResponse, TokenResponse, 
    TokenRefresh, UserQueryParams, UserStatsResponse
)
from app.schemas import SuccessResponse, ErrorResponse
from app.core.security import (
    get_current_user, get_current_active_user, require_permissions,
    create_access_token, create_refresh_token, verify_token,
    hash_password, verify_password
)
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from datetime import datetime, timedelta, timezone
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    current_user: User = Depends(require_permissions(["users:create"]))
):
    """
    Register a new user.
    Requires 'users:create' permission.
    """
    db = database.db
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorCode.USER_ALREADY_EXISTS
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict(exclude={"password"})
    user_dict["password_hash"] = hashed_password
    user_dict["status"] = "active"
    user_dict["is_active"] = True
    user_dict["created_at"] = datetime.now(timezone.utc)
    user_dict["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.users.insert_one(user_dict)
    
    # Fetch created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserResponse(**created_user)

@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin):
    """
    Authenticate user and return access/refresh tokens.
    """
    db = database.db
    
    # Find user by email
    user = await db.users.find_one({"email": user_credentials.email})
    if not user or not verify_password(user_credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_CREDENTIALS
        )
    
    if user.get("status") != "active":
        raise HTTPException(...)
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}}
    )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user["_id"])})
    refresh_token = create_refresh_token(data={"sub": str(user["_id"])})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(**user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(token_data: TokenRefresh):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = verify_token(token_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        db = database.db
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorCode.INVALID_TOKEN
            )
        
        # Create new access token
        access_token = create_access_token(data={"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=token_data.refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user)
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorCode.INVALID_TOKEN
        )

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile with permissions and roles.
    """
    db = database.db
    
    # Get user with populated role and department info
    user_data = await db.users.aggregate([
        {"$match": {"_id": current_user["_id"]}},
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
            status_code=status.HTTP_404_NOT_FOUND,
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
        permissions.extend([p["name"] for p in role_permissions])
    
    # Create response
    profile = UserProfileResponse(**user)
    profile.permissions = list(set(permissions))  # Remove duplicates
    profile.role_names = role_names
    profile.department_name = user.get("department", [{}])[0].get("name") if user.get("department") else None
    
    return profile

@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update current user's profile.
    """
    db = database.db
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.USER_NOT_FOUND
            )
    
    # Return updated user
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return UserResponse(**updated_user)

@router.post("/me/change-password", response_model=SuccessResponse)
async def change_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """
    Change current user's password.
    """
    db = database.db
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_CURRENT_PASSWORD
        )
    
    # Update password
    new_password_hash = hash_password(password_data.new_password)
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {
            "password_hash": new_password_hash,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    return SuccessResponse(message="Password changed successfully")

@router.post("/password-reset-request", response_model=SuccessResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks
):
    """
    Request password reset for user email.
    """
    db = database.db
    
    user = await db.users.find_one({"email": reset_request.email})
    if user and user["is_active"]:
        # Generate reset token and send email
        # TODO: Implement actual email sending
        background_tasks.add_task(send_password_reset_email, user["email"])
    
    # Always return success for security
    return SuccessResponse(message="If the email exists, a reset link has been sent")

@router.get("/", response_model=UserListResponse)
async def list_users(
    params: UserQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    List users with filtering and pagination.
    Requires 'users:read' permission.
    """
    db = database.db
    
    # Build query
    query = {}
    if params.search:
        query["$or"] = [
            {"first_name": {"$regex": params.search, "$options": "i"}},
            {"last_name": {"$regex": params.search, "$options": "i"}},
            {"email": {"$regex": params.search, "$options": "i"}}
        ]
    if params.department_id:
        query["department_id"] = params.department_id
    if params.is_active is not None:
        query["is_active"] = params.is_active
    if params.status:
        query["status"] = params.status
    
    # Count total
    total = await db.users.count_documents(query)
    
    # Calculate pagination
    skip = (params.page - 1) * params.per_page
    pages = (total + params.per_page - 1) // params.per_page
    
    # Get users
    sort_order = 1 if params.sort_order == "asc" else -1
    users = await db.users.find(query).sort(
        params.sort_by, sort_order
    ).skip(skip).limit(params.per_page).to_list(params.per_page)
    
    return UserListResponse(
        users=[UserResponse(**user) for user in users],
        total=total,
        page=params.page,
        per_page=params.per_page,
        pages=pages
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    Get user by ID.
    Requires 'users:read' permission.
    """
    db = database.db
    
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_USER_ID
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.USER_NOT_FOUND
        )
    
    return UserResponse(**user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_permissions(["users:update"]))
):
    """
    Update user by ID.
    Requires 'users:update' permission.
    """
    db = database.db
    
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_USER_ID
        )
    
    # Prepare update data
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        result = await db.users.update_one(
            {"_id": user_obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.USER_NOT_FOUND
            )
    
    # Return updated user
    updated_user = await db.users.find_one({"_id": user_obj_id})
    return UserResponse(**updated_user)

@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permissions(["users:delete"]))
):
    """
    Delete user by ID.
    Requires 'users:delete' permission.
    """
    db = database.db
    
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_USER_ID
        )
    
    # Soft delete user
    result = await db.users.update_one(
        {"_id": user_obj_id},
        {"$set": {
            "is_active": False,
            "status": "deleted",
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.USER_NOT_FOUND
        )
    
    return SuccessResponse(message="User deleted successfully")

@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(require_permissions(["users:read"]))
):
    """
    Get user statistics and analytics.
    Requires 'users:read' permission.
    """
    db = database.db
    
    # Get user counts
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    inactive_users = total_users - active_users
    
    # Get users by department
    department_pipeline = [
        {"$lookup": {
            "from": "departments",
            "localField": "department_id", 
            "foreignField": "_id",
            "as": "department"
        }},
        {"$group": {
            "_id": "$department.name",
            "count": {"$sum": 1}
        }}
    ]
    dept_stats = await db.users.aggregate(department_pipeline).to_list(None)
    users_by_department = {item["_id"][0] if item["_id"] else "Unassigned": item["count"] for item in dept_stats}
    
    # Get recent logins (last 24 hours)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_logins = await db.users.count_documents({
        "last_login": {"$gte": yesterday}
    })
    
    return UserStatsResponse(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        users_by_department=users_by_department,
        users_by_role={},  # TODO: Implement role stats
        recent_logins=recent_logins
    )

# Helper functions
async def send_password_reset_email(email: str):
    """Send password reset email (placeholder)."""
    # TODO: Implement actual email sending
    pass 