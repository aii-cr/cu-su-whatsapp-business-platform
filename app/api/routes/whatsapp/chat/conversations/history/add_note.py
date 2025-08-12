"""Add a note to the conversation history."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from bson import ObjectId
from datetime import datetime

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service, audit_service
from app.core.logger import logger

router = APIRouter()


class AddNoteRequest(BaseModel):
    """Request model for adding a note to conversation history."""
    note: str = Field(..., min_length=1, max_length=1000, description="The note content")


class AddNoteResponse(BaseModel):
    """Response model for adding a note."""
    success: bool
    message: str
    note_id: str


@router.post("/{conversation_id}/history/notes")
async def add_history_note(
    conversation_id: str,
    request: AddNoteRequest,
    current_user: User = Depends(require_permissions(["conversation:write"]))
) -> AddNoteResponse:
    """
    Add a note to the conversation history timeline.
    
    Args:
        conversation_id: The conversation ID
        request: The note request containing the note content
        current_user: The current authenticated user
    
    Returns:
        AddNoteResponse with success status and note ID
    """
    try:
        # Validate conversation exists
        db = await conversation_service._get_db()
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create audit log entry for the note
        correlation_id = f"note-{ObjectId()}"  # Generate a unique ID for this note event
        
        # Get conversation details for audit logging
        customer_phone = conversation.get("customer_phone", "")
        department_id = conversation.get("department_id")
        
        # Use the generic log_event method to include the note content
        await audit_service.log_event(
            action="note_added",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            customer_phone=customer_phone,
            conversation_id=conversation_id,
            department_id=str(department_id) if department_id else None,
            payload={
                "note_id": correlation_id,
                "note_type": "history_note",
                "note_content": request.note
            },
            correlation_id=correlation_id
        )
        
        # Use the correlation_id as the note_id for response
        note_id = correlation_id
        
        logger.info(f"Note added to conversation {conversation_id} by user {current_user.email}")
        
        return AddNoteResponse(
            success=True,
            message="Note added successfully",
            note_id=note_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding note to conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add note")
