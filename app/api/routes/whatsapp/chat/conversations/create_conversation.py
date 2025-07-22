"""Create conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from pprint import pformat

from app.schemas.whatsapp.chat import ConversationCreate, ConversationResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger, log_conversation_event

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(require_permissions(["conversations:create"]))
):
    """
    Create a new conversation.
    Requires 'conversations:create' permission.
    """
    db = database.db
    logger.info(f"[create_conversation] Received payload: {pformat(conversation_data.model_dump())}")
    logger.info(f"[create_conversation] Current user: {pformat(current_user.model_dump())}")
    
    try:
        logger.info("[create_conversation] Checking for existing active conversation...")
        existing_conversation = await db.conversations.find_one({
            "customer_phone": conversation_data.customer_phone,
            "status": {"$in": ["active", "pending"]}
        })
        
        if existing_conversation:
            logger.warning(f"[create_conversation] Active conversation already exists: {pformat(existing_conversation)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.CONVERSATION_ALREADY_ACTIVE
            )
        
        logger.info("[create_conversation] Preparing conversation data for insert...")
        conversation_dict = conversation_data.model_dump()
        conversation_dict.update({
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "message_count": 0,
            "unread_count": 0,
            "created_by": current_user.id
        })
        
        logger.info(f"[create_conversation] Inserting conversation: {pformat(conversation_dict)}")
        result = await db.conversations.insert_one(conversation_dict)
        logger.info(f"[create_conversation] Inserted conversation with id: {result.inserted_id}")
        
        created_conversation = await db.conversations.find_one({"_id": result.inserted_id})
        logger.info(f"[create_conversation] Created conversation: {pformat(created_conversation)}")
        
        log_conversation_event(
            "created", 
            str(result.inserted_id),
            customer_phone=conversation_data.customer_phone,
            created_by=str(current_user.id)
        )
        
        return ConversationResponse(**created_conversation)
        
    except HTTPException as he:
        logger.error(f"[create_conversation] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[create_conversation] Exception: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 