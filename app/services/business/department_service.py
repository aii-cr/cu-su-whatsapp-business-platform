"""Department Service for managing organizational departments."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode


class DepartmentService(BaseService):
    """Service for managing departments."""
    
    def __init__(self):
        super().__init__()
    
    async def create_department(
        self,
        name: str,
        display_name: str,
        description: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        timezone: str = "UTC",
        manager_id: Optional[ObjectId] = None,
        business_hours: Optional[Dict[str, Any]] = None,
        routing_settings: Optional[Dict[str, Any]] = None,
        sla_settings: Optional[Dict[str, Any]] = None,
        auto_assignment_enabled: bool = True,
        max_conversations_per_agent: int = 10,
        tags: Optional[List[str]] = None,
        created_by: ObjectId = None
    ) -> Dict[str, Any]:
        """
        Create a new department.
        
        Args:
            name: Department name (unique)
            display_name: Human-readable department name
            description: Department description
            email: Department contact email
            phone: Department contact phone
            timezone: Department timezone
            manager_id: Department manager user ID
            business_hours: Business hours configuration
            routing_settings: Chat routing configuration
            sla_settings: SLA settings
            auto_assignment_enabled: Enable auto-assignment
            max_conversations_per_agent: Max conversations per agent
            tags: Department tags
            created_by: User who created the department
            
        Returns:
            Created department document
        """
        db = await self._get_db()
        
        # Check for existing department with same name
        existing_department = await db.departments.find_one({"name": name})
        if existing_department:
            raise ValueError(f"Department with name '{name}' already exists")
        
        # Prepare department data
        department_data = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "email": email,
            "phone": phone,
            "timezone": timezone,
            "manager_id": manager_id,
            "status": "active",
            "is_active": True,
            "is_default": False,
            "auto_assignment_enabled": auto_assignment_enabled,
            "max_conversations_per_agent": max_conversations_per_agent,
            "business_hours": business_hours or {
                "timezone": timezone,
                "monday": {"enabled": True, "start": "09:00", "end": "17:00"},
                "tuesday": {"enabled": True, "start": "09:00", "end": "17:00"},
                "wednesday": {"enabled": True, "start": "09:00", "end": "17:00"},
                "thursday": {"enabled": True, "start": "09:00", "end": "17:00"},
                "friday": {"enabled": True, "start": "09:00", "end": "17:00"},
                "saturday": {"enabled": False, "start": "09:00", "end": "17:00"},
                "sunday": {"enabled": False, "start": "09:00", "end": "17:00"}
            },
            "routing_settings": routing_settings or {
                "auto_assignment": auto_assignment_enabled,
                "round_robin": True,
                "max_queue_size": 100,
                "priority_level": 1,
                "escalation_timeout_minutes": 30,
                "require_agent_acceptance": False
            },
            "sla_settings": sla_settings or {
                "first_response_minutes": 5,
                "resolution_hours": 24,
                "escalation_hours": 4,
                "inactivity_timeout_hours": 12
            },
            "whatsapp_settings": {
                "phone_number_id": None,
                "business_account_id": None,
                "welcome_message": "Hello! How can we help you today?",
                "auto_responses_enabled": True,
                "template_namespace": None
            },
            "tags": tags or [],
            "metrics": {
                "total_conversations": 0,
                "active_conversations": 0,
                "average_response_time": 0,
                "satisfaction_rating": 0,
                "resolution_rate": 0
            },
            "user_count": 0,
            "active_user_count": 0,
            "agent_count": 0,
            "active_conversations": 0,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert department
        result = await db.departments.insert_one(department_data)
        department_id = result.inserted_id
        
        logger.info(f"Created department {department_id} with name '{name}'")
        
        # Return created department
        return await db.departments.find_one({"_id": department_id})
    
    async def get_department(self, department_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a department by ID.
        
        Args:
            department_id: Department ID
            
        Returns:
            Department document or None
        """
        try:
            db = await self._get_db()
            obj_id = ObjectId(department_id)
            return await db.departments.find_one({"_id": obj_id})
        except Exception as e:
            logger.error(f"Error getting department {department_id}: {str(e)}")
            return None
    
    async def list_departments(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        List departments with optional filtering.
        
        Args:
            status: Filter by status (active, inactive)
            search: Search in name or display_name
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with departments and pagination info
        """
        db = await self._get_db()
        
        # Build filter
        filter_query = {}
        if status:
            filter_query["status"] = status
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"display_name": {"$regex": search, "$options": "i"}}
            ]
        
        # Count total
        total = await db.departments.count_documents(filter_query)
        
        # Get departments with pagination
        skip = (page - 1) * per_page
        departments = await db.departments.find(filter_query).skip(skip).limit(per_page).to_list(length=None)
        
        return {
            "departments": departments,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def update_department(
        self,
        department_id: str,
        update_data: Dict[str, Any],
        updated_by: ObjectId = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a department.
        
        Args:
            department_id: Department ID
            update_data: Data to update
            updated_by: User who updated the department
            
        Returns:
            Updated department document or None
        """
        try:
            db = await self._get_db()
            obj_id = ObjectId(department_id)
            
            # Check if department exists
            existing_department = await db.departments.find_one({"_id": obj_id})
            if not existing_department:
                return None
            
            # If updating name, check for conflicts
            if "name" in update_data:
                name_conflict = await db.departments.find_one({
                    "name": update_data["name"],
                    "_id": {"$ne": obj_id}
                })
                if name_conflict:
                    raise ValueError(f"Department with name '{update_data['name']}' already exists")
            
            # Add update metadata
            update_data["updated_at"] = datetime.now(timezone.utc)
            if updated_by:
                update_data["updated_by"] = updated_by
            
            # Update department
            result = await db.departments.update_one(
                {"_id": obj_id}, {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return None
            
            logger.info(f"Updated department {department_id}")
            
            # Return updated department
            return await db.departments.find_one({"_id": obj_id})
            
        except Exception as e:
            logger.error(f"Error updating department {department_id}: {str(e)}")
            raise
    
    async def delete_department(self, department_id: str) -> bool:
        """
        Delete a department and unassign its users.
        
        Args:
            department_id: Department ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            db = await self._get_db()
            obj_id = ObjectId(department_id)
            
            # Check if department exists
            department = await db.departments.find_one({"_id": obj_id})
            if not department:
                return False
            
            # Unassign all users from this department
            await db.users.update_many(
                {"department_id": obj_id},
                {"$unset": {"department_id": ""}}
            )
            
            # Update conversations assigned to this department
            await db.conversations.update_many(
                {"department_id": obj_id},
                {"$unset": {"department_id": ""}}
            )
            
            # Delete department
            result = await db.departments.delete_one({"_id": obj_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted department {department_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting department {department_id}: {str(e)}")
            return False
    
    async def add_user_to_department(
        self,
        department_id: str,
        user_id: str
    ) -> bool:
        """
        Add a user to a department.
        
        Args:
            department_id: Department ID
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db = await self._get_db()
            dept_obj_id = ObjectId(department_id)
            user_obj_id = ObjectId(user_id)
            
            # Check if department exists
            department = await db.departments.find_one({"_id": dept_obj_id})
            if not department:
                return False
            
            # Check if user exists
            user = await db.users.find_one({"_id": user_obj_id})
            if not user:
                return False
            
            # Remove user from any other department first
            await db.users.update_one(
                {"_id": user_obj_id},
                {"$unset": {"department_id": ""}}
            )
            
            # Add user to department
            await db.users.update_one(
                {"_id": user_obj_id},
                {"$set": {"department_id": dept_obj_id}}
            )
            
            # Update department user counts
            await self._update_department_user_counts(dept_obj_id)
            
            logger.info(f"Added user {user_id} to department {department_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id} to department {department_id}: {str(e)}")
            return False
    
    async def remove_user_from_department(
        self,
        department_id: str,
        user_id: str
    ) -> bool:
        """
        Remove a user from a department.
        
        Args:
            department_id: Department ID
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db = await self._get_db()
            dept_obj_id = ObjectId(department_id)
            user_obj_id = ObjectId(user_id)
            
            # Remove user from department
            result = await db.users.update_one(
                {"_id": user_obj_id, "department_id": dept_obj_id},
                {"$unset": {"department_id": ""}}
            )
            
            if result.modified_count > 0:
                # Update department user counts
                await self._update_department_user_counts(dept_obj_id)
                logger.info(f"Removed user {user_id} from department {department_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from department {department_id}: {str(e)}")
            return False
    
    async def _update_department_user_counts(self, department_id: ObjectId) -> None:
        """
        Update user counts for a department.
        
        Args:
            department_id: Department ID
        """
        try:
            db = await self._get_db()
            
            # Count total users
            total_users = await db.users.count_documents({"department_id": department_id})
            
            # Count active users
            active_users = await db.users.count_documents({
                "department_id": department_id,
                "status": "active"
            })
            
            # Update department
            await db.departments.update_one(
                {"_id": department_id},
                {"$set": {
                    "user_count": total_users,
                    "active_user_count": active_users
                }}
            )
            
        except Exception as e:
            logger.error(f"Error updating user counts for department {department_id}: {str(e)}")


# Global instance
department_service = DepartmentService() 