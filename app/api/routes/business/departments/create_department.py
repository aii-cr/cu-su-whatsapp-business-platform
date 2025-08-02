from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.business.department import DepartmentCreate, DepartmentResponse
from app.services import department_service, audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(require_permissions(["departments:create"])),
):
    """
    Create a new department.
    Requires 'departments:create' permission.
    """
    try:
        # Prepare department data
        dept_data = {
            "name": department_data.name,
            "display_name": department_data.name,  # Use name as display_name for now
            "description": department_data.description,
            "email": department_data.email,
            "phone": department_data.phone,
            "timezone": department_data.timezone,
            "business_hours": department_data.business_hours,
            "sla_settings": department_data.sla_settings,
            "routing_settings": department_data.routing_settings,
            "auto_assignment_enabled": department_data.auto_assignment_enabled,
            "max_conversations_per_agent": department_data.max_conversations_per_agent,
            "tags": department_data.tags,
            "created_by": current_user.id
        }
        
        # Create department
        department = await department_service.create_department(**dept_data)
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.user_management.log_department_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            department_id=str(department["_id"]),
            department_name=department["name"],
            correlation_id=correlation_id
        )
        
        logger.info(f"Department '{department_data.name}' created by user {current_user.id}")
        
        return DepartmentResponse(**department)
        
    except ValueError as e:
        logger.warning(f"Validation error creating department: {str(e)}")
        error_response = get_error_response(ErrorCode.DEPARTMENT_ALREADY_EXISTS, str(e))
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        )
    except Exception as e:
        logger.error(f"Unexpected error creating department: {str(e)}")
        error_response = get_error_response(ErrorCode.INTERNAL_SERVER_ERROR)
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["detail"]
        ) 