"""Permission and role management utilities."""

from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status
from bson import ObjectId

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from .session_auth import get_current_user


async def get_user_permissions(user_id: ObjectId) -> List[str]:
    """
    Get all permissions for a user through their roles.
    
    Args:
        user_id: User's ObjectId
        
    Returns:
        List of permission keys
    """
    from app.db.client import database
    
    try:
        # Get user's role IDs
        user_doc = await database.db.users.find_one({"_id": user_id}, {"role_ids": 1})
        if not user_doc:
            return []
        
        role_ids = user_doc.get("role_ids", [])
        if not role_ids:
            return []
        
        # Get permissions from all user's roles
        roles = await database.db.roles.find(
            {"_id": {"$in": role_ids}, "is_active": True}
        ).to_list(None)
        
        permission_ids = []
        for role in roles:
            permission_ids.extend(role.get("permission_ids", []))
        
        # Remove duplicates
        permission_ids = list(set(permission_ids))
        
        if not permission_ids:
            return []
        
        # Get permission details
        permissions = await database.db.permissions.find(
            {"_id": {"$in": permission_ids}, "is_active": True}
        ).to_list(None)
        
        return [perm["key"] for perm in permissions]
        
    except Exception as e:
        logger.error(f"Failed to get user permissions: {str(e)}")
        return []


async def get_user_roles(user_id: ObjectId) -> List[Dict[str, Any]]:
    """
    Get all roles for a user.
    
    Args:
        user_id: User's ObjectId
        
    Returns:
        List of role documents
    """
    from app.db.client import database
    
    try:
        # Get user's role IDs
        user_doc = await database.db.users.find_one({"_id": user_id}, {"role_ids": 1})
        if not user_doc:
            return []
        
        role_ids = user_doc.get("role_ids", [])
        if not role_ids:
            return []
        
        # Get role details
        roles = await database.db.roles.find(
            {"_id": {"$in": role_ids}, "is_active": True}
        ).to_list(None)
        
        return roles
        
    except Exception as e:
        logger.error(f"Failed to get user roles: {str(e)}")
        return []


async def check_user_permission(user_id: ObjectId, permission_key: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user_id: User's ObjectId
        permission_key: Permission key to check
        
    Returns:
        True if user has permission, False otherwise
    """
    user_permissions = await get_user_permissions(user_id)
    return permission_key in user_permissions


async def check_user_role(user_id: ObjectId, role_name: str) -> bool:
    """
    Check if a user has a specific role.
    
    Args:
        user_id: User's ObjectId
        role_name: Role name to check
        
    Returns:
        True if user has role, False otherwise
    """
    user_roles = await get_user_roles(user_id)
    role_names = [role["name"] for role in user_roles]
    return role_name in role_names


def require_permissions(required_permissions: List[str]):
    """
    Create a dependency that requires specific permissions.
    
    Args:
        required_permissions: List of permission keys required
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(current_user = Depends(get_current_user)):
        # Super admin bypasses all permission checks
        if current_user.is_super_admin:
            return current_user
        
        # Get user's permissions through roles
        user_permissions = await get_user_permissions(current_user.id)
        
        # Check if user has all required permissions
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_error_response(ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS)["message"],
                )
        
        return current_user
    
    return permission_checker


def require_roles(required_roles: List[str]):
    """
    Create a dependency that requires specific roles.
    
    Args:
        required_roles: List of role names required
        
    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user = Depends(get_current_user)):
        # Super admin bypasses all role checks
        if current_user.is_super_admin:
            return current_user
        
        # Get user's roles
        user_roles = await get_user_roles(current_user.id)
        role_names = [role["name"] for role in user_roles]
        
        # Check if user has any of the required roles
        has_role = any(role in role_names for role in required_roles)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_error_response(ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS)["message"],
            )
        
        return current_user
    
    return role_checker 