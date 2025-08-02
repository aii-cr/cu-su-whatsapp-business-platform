"""
User management audit logging functions.
Provides specific audit logging for user management actions.
"""

from typing import Optional, Dict, Any

class UserManagementAudit:
    """User management specific audit logging methods."""
    
    def __init__(self, audit_service):
        self.audit_service = audit_service
    
    async def log_user_created(
        self,
        actor_id: str,
        actor_name: str,
        created_user_id: str,
        created_user_email: str,
        is_super_admin: bool = False,
        department_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log user creation event."""
        return await self.audit_service.log_event(
            action="user_created",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "created_user_id": created_user_id,
                "created_user_email": created_user_email,
                "is_super_admin": is_super_admin,
                "department_id": department_id,
            },
            correlation_id=correlation_id,
        )
    
    async def log_user_updated(
        self,
        actor_id: str,
        actor_name: str,
        updated_user_id: str,
        updated_user_email: str,
        changes: Dict[str, Any],
        department_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log user update event."""
        return await self.audit_service.log_event(
            action="user_updated",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "updated_user_id": updated_user_id,
                "updated_user_email": updated_user_email,
                "changes": changes,
                "department_id": department_id,
            },
            correlation_id=correlation_id,
        )
    
    async def log_user_deleted(
        self,
        actor_id: str,
        actor_name: str,
        deleted_user_id: str,
        deleted_user_email: str,
        department_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log user deletion event."""
        return await self.audit_service.log_event(
            action="user_deleted",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "deleted_user_id": deleted_user_id,
                "deleted_user_email": deleted_user_email,
                "department_id": department_id,
            },
            correlation_id=correlation_id,
        )
    
    async def log_role_created(
        self,
        actor_id: str,
        actor_name: str,
        role_id: str,
        role_name: str,
        is_system_role: bool = False,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log role creation event."""
        return await self.audit_service.log_event(
            action="role_created",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "role_id": role_id,
                "role_name": role_name,
                "is_system_role": is_system_role,
            },
            correlation_id=correlation_id,
        )
    
    async def log_role_updated(
        self,
        actor_id: str,
        actor_name: str,
        role_id: str,
        role_name: str,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log role update event."""
        return await self.audit_service.log_event(
            action="role_updated",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "role_id": role_id,
                "role_name": role_name,
                "changes": changes,
            },
            correlation_id=correlation_id,
        )
    
    async def log_role_deleted(
        self,
        actor_id: str,
        actor_name: str,
        role_id: str,
        role_name: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log role deletion event."""
        return await self.audit_service.log_event(
            action="role_deleted",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "role_id": role_id,
                "role_name": role_name,
            },
            correlation_id=correlation_id,
        )
    
    async def log_permission_created(
        self,
        actor_id: str,
        actor_name: str,
        permission_id: str,
        permission_key: str,
        permission_name: str,
        is_system_permission: bool = False,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log permission creation event."""
        return await self.audit_service.log_event(
            action="permission_created",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "permission_id": permission_id,
                "permission_key": permission_key,
                "permission_name": permission_name,
                "is_system_permission": is_system_permission,
            },
            correlation_id=correlation_id,
        )
    
    async def log_permission_updated(
        self,
        actor_id: str,
        actor_name: str,
        permission_id: str,
        permission_key: str,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log permission update event."""
        return await self.audit_service.log_event(
            action="permission_updated",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "permission_id": permission_id,
                "permission_key": permission_key,
                "changes": changes,
            },
            correlation_id=correlation_id,
        )
    
    async def log_permission_deleted(
        self,
        actor_id: str,
        actor_name: str,
        permission_id: str,
        permission_key: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log permission deletion event."""
        return await self.audit_service.log_event(
            action="permission_deleted",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "permission_id": permission_id,
                "permission_key": permission_key,
            },
            correlation_id=correlation_id,
        )
    
    async def log_role_assigned(
        self,
        actor_id: str,
        actor_name: str,
        user_id: str,
        user_email: str,
        role_id: str,
        role_name: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log role assignment event."""
        return await self.audit_service.log_event(
            action="role_assigned",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "user_id": user_id,
                "user_email": user_email,
                "role_id": role_id,
                "role_name": role_name,
            },
            correlation_id=correlation_id,
        )
    
    async def log_role_unassigned(
        self,
        actor_id: str,
        actor_name: str,
        user_id: str,
        user_email: str,
        role_id: str,
        role_name: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log role unassignment event."""
        return await self.audit_service.log_event(
            action="role_unassigned",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "user_id": user_id,
                "user_email": user_email,
                "role_id": role_id,
                "role_name": role_name,
            },
            correlation_id=correlation_id,
        )
    
    async def log_department_created(
        self,
        actor_id: str,
        actor_name: str,
        department_id: str,
        department_name: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log department creation event."""
        return await self.audit_service.log_event(
            action="department_created",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "department_id": department_id,
                "department_name": department_name,
            },
            correlation_id=correlation_id,
        )
    
    async def log_department_updated(
        self,
        actor_id: str,
        actor_name: str,
        department_id: str,
        department_name: str,
        changes: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log department update event."""
        return await self.audit_service.log_event(
            action="department_updated",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "department_id": department_id,
                "department_name": department_name,
                "changes": changes,
            },
            correlation_id=correlation_id,
        )
    
    async def log_department_deleted(
        self,
        actor_id: str,
        actor_name: str,
        department_id: str,
        department_name: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log department deletion event."""
        return await self.audit_service.log_event(
            action="department_deleted",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "department_id": department_id,
                "department_name": department_name,
            },
            correlation_id=correlation_id,
        )
    
    async def log_user_added_to_department(
        self,
        actor_id: str,
        actor_name: str,
        department_id: str,
        department_name: str,
        user_id: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log user added to department event."""
        return await self.audit_service.log_event(
            action="user_added_to_department",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "department_id": department_id,
                "department_name": department_name,
                "user_id": user_id,
            },
            correlation_id=correlation_id,
        )
    
    async def log_user_removed_from_department(
        self,
        actor_id: str,
        actor_name: str,
        department_id: str,
        department_name: str,
        user_id: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[str]:
        """Log user removed from department event."""
        return await self.audit_service.log_event(
            action="user_removed_from_department",
            actor_id=actor_id,
            actor_name=actor_name,
            payload={
                "department_id": department_id,
                "department_name": department_name,
                "user_id": user_id,
            },
            correlation_id=correlation_id,
        ) 