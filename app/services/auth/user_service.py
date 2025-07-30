"""User management service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.services.auth import hash_password
from app.schemas.auth.user import UserRegister, UserUpdate

class UserService(BaseService):
    """Service for managing users."""
    
    def __init__(self):
        super().__init__()
    
    async def create_user(
        self,
        user_data: UserRegister,
        created_by: ObjectId,
        is_super_admin: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            user_data: User registration data
            created_by: ID of user creating this user
            is_super_admin: Whether to create as super admin
            
        Returns:
            Created user document
        """
        db = await self._get_db()
        
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Validate role IDs if provided
        role_ids = []
        if user_data.role_ids:
            for role_id in user_data.role_ids:
                role = await db.roles.find_one({"_id": role_id})
                if not role:
                    raise ValueError(f"Role with ID {role_id} not found")
                role_ids.append(role_id)
        
        # Validate department ID if provided
        department_id = None
        if user_data.department_id:
            department = await db.departments.find_one({"_id": user_data.department_id})
            if not department:
                raise ValueError(f"Department with ID {user_data.department_id} not found")
            department_id = user_data.department_id
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Prepare user data
        user_doc = {
            "name": f"{user_data.first_name} {user_data.last_name}",
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email": user_data.email,
            "phone_number": user_data.phone,
            "password_hash": password_hash,
            "role_ids": role_ids,
            "department_id": department_id,
            "is_super_admin": is_super_admin,
            "status": "active",
            "is_active": True,
            "timezone": "UTC",
            "language": "en",
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
            "created_by": created_by,
            "updated_by": created_by
        }
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        user_id = result.inserted_id
        
        logger.info(f"Created user {user_id} for {user_data.email}")
        
        # Return created user
        return await db.users.find_one({"_id": user_id})
    
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
    
    async def update_user(
        self,
        user_id: ObjectId,
        update_data: UserUpdate,
        updated_by: ObjectId
    ) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            update_data: Data to update
            updated_by: User making the update
            
        Returns:
            Updated user document or None
        """
        db = await self._get_db()
        
        # Prepare update data
        update_doc = {}
        
        if update_data.email is not None:
            update_doc["email"] = update_data.email
        if update_data.first_name is not None:
            update_doc["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            update_doc["last_name"] = update_data.last_name
            update_doc["name"] = f"{update_data.first_name} {update_data.last_name}"
        if update_data.phone is not None:
            update_doc["phone_number"] = update_data.phone
        if update_data.department_id is not None:
            update_doc["department_id"] = update_data.department_id
        if update_data.role_ids is not None:
            update_doc["role_ids"] = update_data.role_ids
        if update_data.is_active is not None:
            update_doc["is_active"] = update_data.is_active
        if update_data.preferences is not None:
            update_doc["preferences"] = update_data.preferences
        
        # Add update timestamp
        update_doc["updated_at"] = datetime.now(timezone.utc)
        update_doc["updated_by"] = updated_by
        
        result = await db.users.update_one(
            {"_id": user_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        return await db.users.find_one({"_id": user_id})
    
    async def list_users(
        self,
        search: Optional[str] = None,
        user_id: Optional[ObjectId] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        department_id: Optional[ObjectId] = None,
        role_id: Optional[ObjectId] = None,
        is_active: Optional[bool] = None,
        is_super_admin: Optional[bool] = None,
        status: Optional[str] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        last_login_after: Optional[datetime] = None,
        last_login_before: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List users with comprehensive filtering and pagination.
        
        Args:
            search: Search term
            user_id: Filter by specific user ID
            email: Filter by exact email address
            phone: Filter by phone number
            first_name: Filter by first name
            last_name: Filter by last name
            department_id: Filter by department
            role_id: Filter by role
            is_active: Filter by active status
            is_super_admin: Filter by super admin status
            status: Filter by status
            created_after: Filter users created after this date
            created_before: Filter users created before this date
            last_login_after: Filter users who logged in after this date
            last_login_before: Filter users who logged in before this date
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with users, total count, and pagination info
        """
        db = await self._get_db()
        
        # Build query
        query = {}
        
        if user_id:
            query["_id"] = user_id
        
        if email:
            query["email"] = email
        
        if phone:
            query["phone_number"] = phone
        
        if first_name:
            query["first_name"] = {"$regex": first_name, "$options": "i"}
        
        if last_name:
            query["last_name"] = {"$regex": last_name, "$options": "i"}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}}
            ]
        
        if department_id:
            query["department_id"] = department_id
        
        if role_id:
            query["role_ids"] = role_id
        
        if is_active is not None:
            query["is_active"] = is_active
        
        if is_super_admin is not None:
            query["is_super_admin"] = is_super_admin
        
        if status:
            query["status"] = status
        
        # Date filters
        if created_after or created_before:
            query["created_at"] = {}
            if created_after:
                query["created_at"]["$gte"] = created_after
            if created_before:
                query["created_at"]["$lte"] = created_before
        
        if last_login_after or last_login_before:
            query["last_login"] = {}
            if last_login_after:
                query["last_login"]["$gte"] = last_login_after
            if last_login_before:
                query["last_login"]["$lte"] = last_login_before
        
        # Count total
        total = await db.users.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page
        
        # Get users
        users = await db.users.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

# Global user service instance
user_service = UserService() 