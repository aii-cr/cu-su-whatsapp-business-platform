"""Role management service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.schemas.auth.role import RoleCreate, RoleUpdate

class RoleService(BaseService):
    """Service for managing roles."""
    
    def __init__(self):
        super().__init__()
    
    async def create_role(
        self,
        role_data: RoleCreate,
        created_by: ObjectId
    ) -> Dict[str, Any]:
        """
        Create a new role.
        
        Args:
            role_data: Role creation data
            created_by: ID of user creating this role
            
        Returns:
            Created role document
        """
        db = await self._get_db()
        
        # Check if role name already exists
        existing_role = await db.roles.find_one({"name": role_data.name})
        if existing_role:
            raise ValueError(f"Role with name '{role_data.name}' already exists")
        
        # Validate permission IDs if provided
        permission_ids = []
        if role_data.permission_ids:
            for permission_id in role_data.permission_ids:
                permission = await db.permissions.find_one({"_id": permission_id})
                if not permission:
                    raise ValueError(f"Permission with ID {permission_id} not found")
                permission_ids.append(permission_id)
        
        # Prepare role data
        role_doc = {
            "name": role_data.name,
            "display_name": role_data.name,  # Use name as display name if not provided
            "description": role_data.description,
            "permission_ids": permission_ids,
            "is_system_role": role_data.is_system_role,
            "is_active": role_data.is_active,
            "settings": role_data.settings or {},
            "user_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": created_by,
            "updated_by": created_by
        }
        
        # Insert role
        result = await db.roles.insert_one(role_doc)
        role_id = result.inserted_id
        
        logger.info(f"Created role {role_id} with name '{role_data.name}'")
        
        # Return created role
        return await db.roles.find_one({"_id": role_id})
    
    async def get_role_by_id(self, role_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get role by ID.
        
        Args:
            role_id: Role ID
            
        Returns:
            Role document or None
        """
        db = await self._get_db()
        return await db.roles.find_one({"_id": role_id})
    
    async def get_role_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role document or None
        """
        db = await self._get_db()
        return await db.roles.find_one({"name": name})
    
    async def update_role(
        self,
        role_id: ObjectId,
        update_data: RoleUpdate,
        updated_by: ObjectId
    ) -> Optional[Dict[str, Any]]:
        """
        Update role information.
        
        Args:
            role_id: Role ID
            update_data: Data to update
            updated_by: User making the update
            
        Returns:
            Updated role document or None
        """
        db = await self._get_db()
        
        # Check if role exists
        existing_role = await db.roles.find_one({"_id": role_id})
        if not existing_role:
            return None
        
        # Prevent updating system roles unless super admin
        if existing_role.get("is_system_role") and not updated_by:  # TODO: Check if user is super admin
            raise ValueError("Cannot update system roles without super admin privileges")
        
        # Prepare update data
        update_doc = {}
        
        if update_data.name is not None:
            # Check if new name conflicts with existing role
            if update_data.name != existing_role["name"]:
                conflict_role = await db.roles.find_one({"name": update_data.name})
                if conflict_role:
                    raise ValueError(f"Role with name '{update_data.name}' already exists")
            update_doc["name"] = update_data.name
            update_doc["display_name"] = update_data.name
        
        if update_data.description is not None:
            update_doc["description"] = update_data.description
        
        if update_data.permission_ids is not None:
            # Validate permission IDs
            permission_ids = []
            for permission_id in update_data.permission_ids:
                permission = await db.permissions.find_one({"_id": permission_id})
                if not permission:
                    raise ValueError(f"Permission with ID {permission_id} not found")
                permission_ids.append(permission_id)
            update_doc["permission_ids"] = permission_ids
        
        if update_data.is_active is not None:
            update_doc["is_active"] = update_data.is_active
        
        if update_data.settings is not None:
            update_doc["settings"] = update_data.settings
        
        # Add update timestamp
        update_doc["updated_at"] = datetime.now(timezone.utc)
        update_doc["updated_by"] = updated_by
        
        result = await db.roles.update_one(
            {"_id": role_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        return await db.roles.find_one({"_id": role_id})
    
    async def delete_role(self, role_id: ObjectId, deleted_by: ObjectId) -> bool:
        """
        Delete a role.
        
        Args:
            role_id: Role ID
            deleted_by: User deleting the role
            
        Returns:
            True if deleted successfully
        """
        db = await self._get_db()
        
        # Check if role exists
        role = await db.roles.find_one({"_id": role_id})
        if not role:
            return False
        
        # Prevent deleting system roles
        if role.get("is_system_role"):
            raise ValueError("Cannot delete system roles")
        
        # Check if role is assigned to any users
        users_with_role = await db.users.count_documents({"role_ids": role_id})
        if users_with_role > 0:
            raise ValueError(f"Cannot delete role '{role['name']}' - it is assigned to {users_with_role} user(s)")
        
        # Delete role
        result = await db.roles.delete_one({"_id": role_id})
        
        return result.deleted_count > 0
    
    async def list_roles(
        self,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system_role: Optional[bool] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List roles with filtering and pagination.
        
        Args:
            search: Search term
            is_active: Filter by active status
            is_system_role: Filter by system role status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with roles, total count, and pagination info
        """
        db = await self._get_db()
        
        # Build query
        query = {}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"display_name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        if is_active is not None:
            query["is_active"] = is_active
        
        if is_system_role is not None:
            query["is_system_role"] = is_system_role
        
        # Count total
        total = await db.roles.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page
        
        # Get roles
        roles = await db.roles.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
        
        return {
            "roles": roles,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

# Global role service instance
role_service = RoleService() 