"""System audit service for managing audit logs."""

import math
from datetime import datetime
from typing import Any, Dict, Optional, List
from bson import ObjectId

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode
from app.schemas.system.audit_log import WhatsAppAuditQueryParams


class SystemAuditService(BaseService):
    """Service for managing system audit logs."""
    
    async def get_audit_logs(
        self,
        page: int = 1,
        per_page: int = 50,
        action: Optional[str] = None,
        actor_id: Optional[ObjectId] = None,
        actor_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        conversation_id: Optional[ObjectId] = None,
        department_id: Optional[ObjectId] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        Get audit logs with filtering and pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            action: Filter by action type
            actor_id: Filter by actor ID
            actor_name: Filter by actor name
            customer_phone: Filter by customer phone
            conversation_id: Filter by conversation ID
            department_id: Filter by department ID
            from_date: Filter logs from this date
            to_date: Filter logs to this date
            correlation_id: Filter by correlation ID
            sort_by: Sort field
            sort_order: Sort order (asc/desc)
            
        Returns:
            Dictionary with logs, pagination info, and metadata
        """
        await self._ensure_db_connection()
        
        # Build query parameters
        query_params = WhatsAppAuditQueryParams(
            page=page,
            per_page=per_page,
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=department_id,
            from_date=from_date,
            to_date=to_date,
            correlation_id=correlation_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # Build MongoDB query
        mongo_query = await self._build_mongo_query(query_params)
        
        # Build sort criteria
        sort_criteria = await self._build_sort_criteria(query_params)
        
        # Calculate pagination
        skip = (query_params.page - 1) * query_params.per_page
        limit = query_params.per_page
        
        # Execute queries in parallel
        logs_cursor = self.db.audit_logs.find(mongo_query).sort(sort_criteria).skip(skip).limit(limit)
        logs = await logs_cursor.to_list(length=limit)
        total_count = await self.db.audit_logs.count_documents(mongo_query)
        
        # Calculate total pages
        total_pages = math.ceil(total_count / query_params.per_page)
        
        return {
            "logs": logs,
            "total": total_count,
            "page": query_params.page,
            "per_page": query_params.per_page,
            "pages": total_pages,
            "filters": {
                "action": query_params.action,
                "actor_id": query_params.actor_id,
                "conversation_id": query_params.conversation_id,
                "from_date": query_params.from_date,
                "to_date": query_params.to_date,
            }
        }
    
    async def _build_mongo_query(self, params: WhatsAppAuditQueryParams) -> Dict[str, Any]:
        """
        Build MongoDB query from query parameters.
        
        Args:
            params: Validated query parameters
            
        Returns:
            MongoDB query dictionary
        """
        query = {}
        
        # Filter by action
        if params.action:
            query["action"] = params.action
        
        # Filter by actor
        if params.actor_id:
            query["actor_id"] = params.actor_id
        
        if params.actor_name:
            query["actor_name"] = {"$regex": params.actor_name, "$options": "i"}
        
        # Filter by customer phone
        if params.customer_phone:
            query["customer_phone"] = params.customer_phone
        
        # Filter by conversation
        if params.conversation_id:
            query["conversation_id"] = params.conversation_id
        
        # Filter by department
        if params.department_id:
            query["department_id"] = params.department_id
        
        # Filter by date range
        date_filter = {}
        if params.from_date:
            date_filter["$gte"] = params.from_date
        if params.to_date:
            date_filter["$lte"] = params.to_date
        
        if date_filter:
            query["created_at"] = date_filter
        
        # Filter by correlation ID in metadata
        if params.correlation_id:
            query["metadata.correlation_id"] = params.correlation_id
        
        return query
    
    async def _build_sort_criteria(self, params: WhatsAppAuditQueryParams) -> list:
        """
        Build MongoDB sort criteria from query parameters.
        
        Args:
            params: Validated query parameters
            
        Returns:
            MongoDB sort criteria list
        """
        # Validate sort field
        valid_sort_fields = ["created_at", "action", "actor_name", "customer_phone"]
        
        sort_field = params.sort_by if params.sort_by in valid_sort_fields else "created_at"
        sort_direction = -1 if params.sort_order == "desc" else 1
        
        return [(sort_field, sort_direction)]
    
    async def create_audit_log(
        self,
        action: str,
        actor_id: ObjectId,
        actor_name: str,
        resource_type: str,
        resource_id: ObjectId,
        details: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """
        Create a new audit log entry.
        
        Args:
            action: Action performed
            actor_id: ID of the user performing the action
            actor_name: Name of the user performing the action
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            details: Details about the action
            metadata: Additional metadata
            
        Returns:
            ID of the created audit log
        """
        await self._ensure_db_connection()
        
        audit_log = {
            "action": action,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "level": "info",
            "success": True
        }
        
        result = await self.db.audit_logs.insert_one(audit_log)
        return result.inserted_id