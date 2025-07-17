"""Conversation management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from app.schemas.chat import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationListResponse, ConversationQueryParams, ConversationStatsResponse
)
from app.schemas import SuccessResponse
from app.core.security import get_current_active_user, require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger, log_conversation_event

router = APIRouter(prefix="/conversations", tags=["Conversations"])

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
    
    try:
        # Check if active conversation already exists for this customer
        existing_conversation = await db.conversations.find_one({
            "customer_phone": conversation_data.customer_phone,
            "status": {"$in": ["active", "pending"]}
        })
        
        if existing_conversation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorCode.CONVERSATION_ALREADY_ACTIVE
            )
        
        # Prepare conversation data
        conversation_dict = conversation_data.dict()
        conversation_dict.update({
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "unread_count": 0,
            "created_by": current_user["_id"]
        })
        
        # Insert conversation
        result = await db.conversations.insert_one(conversation_dict)
        
        # Fetch created conversation
        created_conversation = await db.conversations.find_one({"_id": result.inserted_id})
        
        # Log conversation creation
        log_conversation_event(
            "created", 
            str(result.inserted_id),
            customer_phone=conversation_data.customer_phone,
            created_by=str(current_user["_id"])
        )
        
        return ConversationResponse(**created_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    params: ConversationQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    List conversations with filtering and pagination.
    Requires 'conversations:read' permission.
    """
    db = database.db
    
    try:
        # Build query
        query = {}
        if params.search:
            query["$or"] = [
                {"customer_name": {"$regex": params.search, "$options": "i"}},
                {"customer_phone": {"$regex": params.search, "$options": "i"}}
            ]
        if params.status:
            query["status"] = params.status
        if params.priority:
            query["priority"] = params.priority
        if params.channel:
            query["channel"] = params.channel
        if params.department_id:
            query["department_id"] = params.department_id
        if params.assigned_agent_id:
            query["assigned_agent_id"] = params.assigned_agent_id
        if params.customer_type:
            query["customer_type"] = params.customer_type
        if params.has_unread:
            query["unread_count"] = {"$gt": 0} if params.has_unread else {"$eq": 0}
        if params.created_from:
            query.setdefault("created_at", {})["$gte"] = params.created_from
        if params.created_to:
            query.setdefault("created_at", {})["$lte"] = params.created_to
        if params.tags:
            query["tags"] = {"$in": params.tags}
        
        # Count total
        total = await db.conversations.count_documents(query)
        
        # Calculate pagination
        skip = (params.page - 1) * params.per_page
        pages = (total + params.per_page - 1) // params.per_page
        
        # Get conversations
        sort_order = 1 if params.sort_order == "asc" else -1
        conversations = await db.conversations.find(query).sort(
            params.sort_by, sort_order
        ).skip(skip).limit(params.per_page).to_list(params.per_page)
        
        return ConversationListResponse(
            conversations=[ConversationResponse(**conv) for conv in conversations],
            total=total,
            page=params.page,
            per_page=params.per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get conversation by ID.
    Requires 'conversations:read' permission.
    """
    db = database.db
    
    try:
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_CONVERSATION_ID
        )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.CONVERSATION_NOT_FOUND
        )
    
    return ConversationResponse(**conversation)

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(require_permissions(["conversations:update"]))
):
    """
    Update conversation by ID.
    Requires 'conversations:update' permission.
    """
    db = database.db
    
    try:
        conversation_obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_CONVERSATION_ID
        )
    
    # Prepare update data
    update_data = conversation_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = current_user["_id"]
        
        result = await db.conversations.update_one(
            {"_id": conversation_obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Log conversation update
        log_conversation_event(
            "updated",
            conversation_id,
            updated_by=str(current_user["_id"]),
            changes=list(update_data.keys())
        )
    
    # Return updated conversation
    updated_conversation = await db.conversations.find_one({"_id": conversation_obj_id})
    return ConversationResponse(**updated_conversation)

@router.get("/stats/overview", response_model=ConversationStatsResponse)
async def get_conversation_statistics(
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get conversation statistics and analytics.
    Requires 'conversations:read' permission.
    """
    db = database.db
    
    try:
        # Get conversation counts
        total_conversations = await db.conversations.count_documents({})
        active_conversations = await db.conversations.count_documents({"status": "active"})
        closed_conversations = await db.conversations.count_documents({"status": "closed"})
        unassigned_conversations = await db.conversations.count_documents({"assigned_agent_id": None})
        
        # Get conversations by status
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_stats = await db.conversations.aggregate(status_pipeline).to_list(None)
        conversations_by_status = {item["_id"]: item["count"] for item in status_stats}
        
        # Get conversations by priority
        priority_pipeline = [
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        priority_stats = await db.conversations.aggregate(priority_pipeline).to_list(None)
        conversations_by_priority = {item["_id"]: item["count"] for item in priority_stats}
        
        # Get conversations by channel
        channel_pipeline = [
            {"$group": {"_id": "$channel", "count": {"$sum": 1}}}
        ]
        channel_stats = await db.conversations.aggregate(channel_pipeline).to_list(None)
        conversations_by_channel = {item["_id"]: item["count"] for item in channel_stats}
        
        return ConversationStatsResponse(
            total_conversations=total_conversations,
            active_conversations=active_conversations,
            closed_conversations=closed_conversations,
            unassigned_conversations=unassigned_conversations,
            conversations_by_status=conversations_by_status,
            conversations_by_priority=conversations_by_priority,
            conversations_by_channel=conversations_by_channel,
            average_response_time_minutes=0.0,  # TODO: Calculate from messages
            average_resolution_time_minutes=0.0,  # TODO: Calculate from closed conversations
            customer_satisfaction_rate=0.0  # TODO: Calculate from surveys
        )
        
    except Exception as e:
        logger.error(f"Failed to get conversation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 