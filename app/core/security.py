"""
Security utilities for JWT authentication and RBAC authorization.
Provides password hashing, token generation/validation, and permission checking.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from bson import ObjectId

from app.core.config import settings
from app.core.logger import logger
from app.config.error_codes import ErrorCode, get_error_response


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security scheme
security = HTTPBearer()


class TokenData:
    """Token data structure for JWT tokens."""
    
    def __init__(self, user_id: str = None, email: str = None, scopes: List[str] = None):
        self.user_id = user_id
        self.email = email
        self.scopes = scopes or []


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Type of token ("access" or "refresh")
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
            
        # Check expiration
        if datetime.now(timezone.utc) > datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc):
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        return None


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Extract and validate the current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        scopes: List[str] = payload.get("scopes", [])
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return TokenData(user_id=user_id, email=email, scopes=scopes)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token_data: TokenData = Depends(get_current_user_token)):
    """
    Get the current authenticated user from the database.
    
    Args:
        token_data: Token data from JWT
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If user not found or inactive
    """
    from app.db.client import database
    from app.db.models.auth.user import User, UserStatus
    
    try:
        user_id = ObjectId(token_data.user_id)
        user_doc = await database.db.users.find_one({"_id": user_id})
        
        if not user_doc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_USER_NOT_FOUND)["message"],
            )
        
        user = User(**user_doc)
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=get_error_response(ErrorCode.AUTH_USER_INACTIVE)["message"],
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_error_response(ErrorCode.AUTH_TOKEN_INVALID)["message"],
        )


async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Get the current active user (alias for get_current_user for clarity).
    
    Args:
        current_user: Current user from dependency
        
    Returns:
        Active user object
    """
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Create a dependency that requires specific permissions.
    
    Args:
        required_permissions: List of permission keys required
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(current_user = Depends(get_current_user)):
        from app.db.client import database
        
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
        from app.db.client import database
        
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


# Common permission dependencies
RequireLogin = Depends(get_current_active_user)
RequireAdmin = require_roles(["admin"])
RequireSupervisor = require_roles(["admin", "supervisor"])
RequireAgent = require_roles(["admin", "supervisor", "agent"])

# Common permission-based dependencies
RequireUserManagement = require_permissions(["users.create", "users.update", "users.delete"])
RequireConversationAccess = require_permissions(["conversations.read"])
RequireMessageSend = require_permissions(["messages.create"])
RequireMediaUpload = require_permissions(["media.upload"])
RequireSystemAdmin = require_permissions(["system.admin"])

