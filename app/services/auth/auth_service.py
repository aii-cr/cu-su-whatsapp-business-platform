"""Authentication service for user management and authentication."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.services.auth.utils.session_auth import create_session_token
from app.services.auth.utils.password_utils import verify_password
from app.core.config import settings


class AuthService(BaseService):
    """Service for managing user authentication and authorization."""
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            User document if authentication successful, None otherwise
        """
        db = await self._get_db()
        
        # Find user by email
        user = await db.users.find_one({"email": email})
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return None
        
        # Check if user is active
        if user.get("status") != "active":
            return None
        
        return user
    
    async def update_last_login(self, user_id: ObjectId) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            True if updated successfully
        """
        db = await self._get_db()
        
        result = await db.users.update_one(
            {"_id": user_id},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        return result.modified_count > 0
    
    async def get_user_profile(self, user_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get user profile with populated role and department info.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile with roles and permissions
        """
        db = await self._get_db()
        
        # Get user with populated role and department info
        user_data = await db.users.aggregate([
            {"$match": {"_id": user_id}},
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
            return None
        
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
        
        # Add profile data
        user["permissions"] = list(set(permissions))  # Remove duplicates
        user["role_names"] = role_names
        user["department_name"] = user.get("department", [{}])[0].get("name") if user.get("department") else None
        
        return user
    
    async def create_session_token(self, user_id: ObjectId, email: str = None) -> str:
        """
        Create session token for user.
        
        Args:
            user_id: User ID
            email: User's email (optional)
            
        Returns:
            Session token string
        """
        token_data = {"sub": str(user_id)}
        if email:
            token_data["email"] = email
            
        return create_session_token(data=token_data)
    
    async def get_user_by_id(self, user_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User document or None
        """
        db = await self._get_db()
        return await db.users.find_one({"_id": user_id})
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: User's email
            
        Returns:
            User document or None
        """
        db = await self._get_db()
        return await db.users.find_one({"email": email})
    
    async def update_user(self, user_id: ObjectId, update_data: Dict[str, Any]) -> bool:
        """
        Update user information.
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            True if updated successfully
        """
        db = await self._get_db()
        
        result = await db.users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0


# Global auth service instance
auth_service = AuthService()