"""Get conversation statistics endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.whatsapp.chat import ConversationStatsResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services import websocket_service

router = APIRouter()

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
        
        stats_response = ConversationStatsResponse(
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
        
        # Broadcast stats update to dashboard subscribers
        try:
            await websocket_service.notify_dashboard_stats_update(stats_response.dict())
            logger.info("📊 [STATS] Broadcasted stats update to dashboard subscribers")
        except Exception as e:
            logger.error(f"Failed to broadcast stats update: {str(e)}")
        
        return stats_response
        
    except Exception as e:
        logger.error(f"Failed to get conversation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 