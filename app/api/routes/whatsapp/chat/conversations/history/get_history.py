"""Get aggregated conversation history endpoint with enhanced user tracking."""

from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from bson import ObjectId

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service
from app.core.logger import logger

router = APIRouter()


def get_user_info(user_id: str, users_cache: Dict[str, Dict]) -> Dict[str, str]:
    """Get user information from cache or database."""
    if user_id in users_cache:
        user = users_cache[user_id]
        name = user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        email = user.get('email', '')
        return {"name": name or email or user_id, "email": email}
    return {"name": user_id, "email": ""}


@router.get("/{conversation_id}/history")
async def get_history(
    conversation_id: str,
    include_access_logs: bool = False,
    include_messages: bool = False,
    current_user: User = Depends(require_permissions(["conversations:read"]))
) -> Dict[str, Any]:
    """
    Get comprehensive conversation history including messages and all audit events.
    Returns enhanced data with user names and emails for better tracking.
    """
    try:
        db = await conversation_service._get_db()
        
        # Create users cache for faster lookups
        users_cache = {}
        users_cursor = db.users.find({})
        async for user in users_cursor:
            users_cache[str(user["_id"])] = user
        
        # Get messages only if requested
        msgs = []
        if include_messages:
            msgs = await db.messages.find({"conversation_id": ObjectId(conversation_id)}).sort("timestamp", 1).to_list(1000)
        
        # Get audit events - exclude conversation_accessed by default
        audit_filter = {
            "conversation_id": ObjectId(conversation_id)
        }
        
        if not include_access_logs:
            # Exclude conversation access logs unless specifically requested
            audit_filter["action"] = {"$ne": "conversation_accessed"}
        
        audits = await db.audit_logs.find(audit_filter).sort("created_at", 1).to_list(1000)

        # Get conversation details for customer info
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        customer_name = conversation.get("customer_name", "") if conversation else ""
        customer_phone = conversation.get("customer_phone", "") if conversation else ""
        
        items = []
        
        # Process messages
        for m in msgs:
            sender_id = str(m.get("sender_id", ""))
            direction = m.get("direction", "unknown")
            
            # For outbound messages, use customer info; for inbound, use agent info  
            if direction == "outbound":
                actor_name = f"{customer_name} ({customer_phone})" if customer_name else customer_phone
                actor_email = ""
            else:
                user_info = get_user_info(sender_id, users_cache) if sender_id else {"name": "Unknown", "email": ""}
                actor_name = user_info["name"]
                actor_email = user_info["email"]
            
            # Process message content
            text_content = m.get("text_content", "")
            msg_type = m.get("message_type", "text")
            
            # For media messages, show "Media message"
            if msg_type != "text":
                display_text = "Media message"
            else:
                # Truncate long text messages  
                display_text = text_content[:100] + "..." if len(text_content) > 100 else text_content
            
            items.append({
                "type": f"message_{direction}",
                "ts_utc": m.get("timestamp"),
                "actor_name": actor_name,
                "actor_email": actor_email,
                "payload": {
                    "text": display_text,
                    "full_text": text_content,  # Keep full content for export
                    "status": m.get("status"),
                    "direction": direction,
                    "message_type": msg_type
                }
            })
        
        # Process audit logs
        for a in audits:
            actor_id = str(a.get("actor_id", ""))
            user_info = get_user_info(actor_id, users_cache) if actor_id else {"name": a.get("actor_name", "System"), "email": ""}
            
            items.append({
                "type": a.get("action"),
                "ts_utc": a.get("created_at"),
                "actor_name": user_info["name"],
                "actor_email": user_info["email"],
                "payload": a.get("payload", {}),
                "details": a.get("details", "")
            })

        # Sort by timestamp
        items.sort(key=lambda x: x.get("ts_utc") or 0)
        
        logger.info(f"Retrieved {len(items)} history items for conversation {conversation_id}")
        
        return {"conversation_id": conversation_id, "items": items}
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}")
        return {"conversation_id": conversation_id, "items": [], "error": "Failed to load history"}


