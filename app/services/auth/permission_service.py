"""Permission management service."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.schemas.auth.permission import PermissionCreate, PermissionUpdate

class PermissionService(BaseService):
    """Service for managing permissions."""
    
    def __init__(self):
        super().__init__()
    
    async def create_permission(
        self,
        permission_data: PermissionCreate,
        created_by: ObjectId
    ) -> Dict[str, Any]:
        """
        Create a new permission.
        
        Args:
            permission_data: Permission creation data
            created_by: ID of user creating this permission
            
        Returns:
            Created permission document
        """
        db = await self._get_db()
        
        # Check if permission key already exists
        existing_permission = await db.permissions.find_one({"key": permission_data.name})
        if existing_permission:
            raise ValueError(f"Permission with key '{permission_data.name}' already exists")
        
        # Prepare permission data
        permission_doc = {
            "key": permission_data.name,  # Use name as key
            "name": permission_data.name,
            "description": permission_data.description,
            "category": permission_data.category,
            "action": permission_data.action,
            "resource": permission_data.resource,
            "is_system_permission": permission_data.is_system_permission,
            "is_active": True,
            "requires_approval": False,
            "scope": {
                "department_scoped": False,
                "self_only": False,
                "conditions": []
            },
            "role_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": created_by,
            "updated_by": created_by
        }
        
        # Insert permission
        result = await db.permissions.insert_one(permission_doc)
        permission_id = result.inserted_id
        
        logger.info(f"Created permission {permission_id} with key '{permission_data.name}'")
        
        # Return created permission
        return await db.permissions.find_one({"_id": permission_id})
    
    async def get_permission_by_id(self, permission_id: ObjectId) -> Optional[Dict[str, Any]]:
        """
        Get permission by ID.
        
        Args:
            permission_id: Permission ID
            
        Returns:
            Permission document or None
        """
        db = await self._get_db()
        return await db.permissions.find_one({"_id": permission_id})
    
    async def get_permission_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get permission by key.
        
        Args:
            key: Permission key
            
        Returns:
            Permission document or None
        """
        db = await self._get_db()
        return await db.permissions.find_one({"key": key})
    
    async def update_permission(
        self,
        permission_id: ObjectId,
        update_data: PermissionUpdate,
        updated_by: ObjectId
    ) -> Optional[Dict[str, Any]]:
        """
        Update permission information.
        
        Args:
            permission_id: Permission ID
            update_data: Data to update
            updated_by: User making the update
            
        Returns:
            Updated permission document or None
        """
        db = await self._get_db()
        
        # Check if permission exists
        existing_permission = await db.permissions.find_one({"_id": permission_id})
        if not existing_permission:
            return None
        
        # Prevent updating system permissions unless super admin
        if existing_permission.get("is_system_permission") and not updated_by:  # TODO: Check if user is super admin
            raise ValueError("Cannot update system permissions without super admin privileges")
        
        # Prepare update data
        update_doc = {}
        
        if update_data.name is not None:
            # Check if new name conflicts with existing permission
            if update_data.name != existing_permission["name"]:
                conflict_permission = await db.permissions.find_one({"key": update_data.name})
                if conflict_permission:
                    raise ValueError(f"Permission with key '{update_data.name}' already exists")
            update_doc["name"] = update_data.name
            update_doc["key"] = update_data.name
        
        if update_data.description is not None:
            update_doc["description"] = update_data.description
        
        if update_data.category is not None:
            update_doc["category"] = update_data.category
        
        if update_data.action is not None:
            update_doc["action"] = update_data.action
        
        if update_data.resource is not None:
            update_doc["resource"] = update_data.resource
        
        if update_data.conditions is not None:
            update_doc["conditions"] = update_data.conditions
        
        # Add update timestamp
        update_doc["updated_at"] = datetime.now(timezone.utc)
        update_doc["updated_by"] = updated_by
        
        result = await db.permissions.update_one(
            {"_id": permission_id},
            {"$set": update_doc}
        )
        
        if result.modified_count == 0:
            return None
        
        return await db.permissions.find_one({"_id": permission_id})
    
    async def delete_permission(self, permission_id: ObjectId, deleted_by: ObjectId) -> bool:
        """
        Delete a permission.
        
        Args:
            permission_id: Permission ID
            deleted_by: User deleting the permission
            
        Returns:
            True if deleted successfully
        """
        db = await self._get_db()
        
        # Check if permission exists
        permission = await db.permissions.find_one({"_id": permission_id})
        if not permission:
            return False
        
        # Prevent deleting system permissions
        if permission.get("is_system_permission"):
            raise ValueError("Cannot delete system permissions")
        
        # Check if permission is assigned to any roles
        roles_with_permission = await db.roles.count_documents({"permission_ids": permission_id})
        if roles_with_permission > 0:
            raise ValueError(f"Cannot delete permission '{permission['key']}' - it is assigned to {roles_with_permission} role(s)")
        
        # Delete permission
        result = await db.permissions.delete_one({"_id": permission_id})
        
        return result.deleted_count > 0
    
    async def list_permissions(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system_permission: Optional[bool] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List permissions with filtering and pagination.
        
        Args:
            search: Search term
            category: Filter by category
            action: Filter by action
            resource: Filter by resource
            is_active: Filter by active status
            is_system_permission: Filter by system permission status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with permissions, total count, and pagination info
        """
        db = await self._get_db()
        
        # Build query
        query = {}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"key": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        if category:
            query["category"] = category
        
        if action:
            query["action"] = action
        
        if resource:
            query["resource"] = resource
        
        if is_active is not None:
            query["is_active"] = is_active
        
        if is_system_permission is not None:
            query["is_system_permission"] = is_system_permission
        
        # Count total
        total = await db.permissions.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        pages = (total + per_page - 1) // per_page
        
        # Get permissions
        permissions = await db.permissions.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
        
        return {
            "permissions": permissions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

# Global permission service instance
permission_service = PermissionService() 