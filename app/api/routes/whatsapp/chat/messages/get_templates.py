"""Get WhatsApp message templates endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.whatsapp.chat.message_out import TemplateListResponse
from app.services import whatsapp_service

router = APIRouter()

# WhatsApp service is imported from app.services

@router.get("/templates", response_model=TemplateListResponse)
async def get_available_templates(
    current_user: User = Depends(require_permissions(["messages:read_template"]))
):
    """
    Get available WhatsApp message templates.
    Requires 'messages:read_template' permission.
    """
    try:
        templates = await whatsapp_service.get_message_templates()
        
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
        
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 