"""Export conversation history as PDF with enhanced formatting and filtering options."""

from fastapi import APIRouter, Depends, Response, Query
from reportlab.lib.pagesizes import LETTER, A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from io import BytesIO
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
import textwrap

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import conversation_service
from app.core.logger import logger

router = APIRouter()


def wrap_text(text: str, max_width: int = 60) -> List[str]:
    """Wrap text to prevent cutting off in PDF."""
    if not text:
        return [""]
    return textwrap.wrap(text, width=max_width)


def format_timestamp(timestamp) -> str:
    """Format timestamp for better readability."""
    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return str(timestamp)
    elif hasattr(timestamp, 'strftime'):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    return str(timestamp)


def get_user_info(user_id: str, users_cache: dict) -> str:
    """Get user name and email from cache."""
    if user_id in users_cache:
        user = users_cache[user_id]
        name = user.get('name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        email = user.get('email', '')
        if name and email:
            return f"{name} ({email})"
        elif name:
            return name
        elif email:
            return email
    return user_id


@router.get("/{conversation_id}/history/export")
async def export_history_pdf(
    conversation_id: str,
    export_type: str = Query("all", description="Type of export: all, messages, transfers, actions"),
    current_user: User = Depends(require_permissions(["conversation:export"]))
):
    """
    Export conversation history as a formatted PDF.
    
    Args:
        conversation_id: The conversation ID
        export_type: What to include in the export:
            - "all": All messages and activities
            - "messages": Only messages
            - "transfers": Only agent transfers and participant changes
            - "actions": Only conversation actions (status changes, notes, etc.)
    """
    try:
        db = await conversation_service._get_db()
        
        # Get conversation details
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
        if not conversation:
            return Response("Conversation not found", status_code=404)
        
        # Create users cache for faster lookups
        users_cache = {}
        users_cursor = db.users.find({})
        async for user in users_cursor:
            users_cache[str(user["_id"])] = user
        
        items = []
        
        # Fetch messages if needed
        if export_type in ["all", "messages"]:
            msgs = await db.messages.find({"conversation_id": ObjectId(conversation_id)}).sort("timestamp", 1).to_list(1000)
            for m in msgs:
                sender_info = get_user_info(m.get('sender_id', ''), users_cache) if m.get('sender_id') else m.get('sender_name', 'Unknown')
                items.append({
                    "timestamp": m.get("timestamp"),
                    "type": "message",
                    "direction": m.get("direction", "unknown"),
                    "sender": sender_info,
                    "content": m.get('text_content', ''),
                    "status": m.get("status", "")
                })
        
        # Fetch audit logs if needed
        if export_type in ["all", "transfers", "actions"]:
            audits = await db.audit_logs.find({"conversation_id": ObjectId(conversation_id)}).sort("created_at", 1).to_list(1000)
            for a in audits:
                action = a.get('action', '')
                
                # Filter based on export type
                if export_type == "transfers" and not any(keyword in action.lower() for keyword in ["transfer", "participant", "assign"]):
                    continue
                elif export_type == "actions" and any(keyword in action.lower() for keyword in ["transfer", "participant", "message"]):
                    continue
                
                actor_info = get_user_info(a.get('actor_id', ''), users_cache) if a.get('actor_id') else a.get('actor_name', 'System')
                items.append({
                    "timestamp": a.get("created_at"),
                    "type": "audit",
                    "action": action,
                    "actor": actor_info,
                    "payload": a.get('payload', {}),
                    "details": a.get('details', '')
                })
        
        # Sort by timestamp
        items.sort(key=lambda x: x.get("timestamp") or datetime.min)
        
        # Create PDF with better formatting
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=6,
            spaceAfter=6
        )
        
        # Build the story
        story = []
        
        # Title
        story.append(Paragraph(f"Conversation History Report", title_style))
        story.append(Spacer(1, 12))
        
        # Conversation info
        customer_name = conversation.get('customer_name') or conversation.get('customer', {}).get('name', 'Unknown')
        story.append(Paragraph(f"<b>Conversation ID:</b> {conversation_id}", body_style))
        story.append(Paragraph(f"<b>Customer:</b> {customer_name}", body_style))
        story.append(Paragraph(f"<b>Status:</b> {conversation.get('status', 'Unknown')}", body_style))
        story.append(Paragraph(f"<b>Export Type:</b> {export_type.title()}", body_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
        generated_by_name = current_user.name or current_user.email
        story.append(Paragraph(f"<b>Generated by:</b> {generated_by_name} ({current_user.email})", body_style))
        story.append(Spacer(1, 20))
        
        # Timeline
        story.append(Paragraph("Timeline", header_style))
        
        for item in items:
            timestamp_str = format_timestamp(item.get("timestamp"))
            
            if item.get("type") == "message":
                direction_icon = "→" if item.get("direction") == "outbound" else "←"
                sender = item.get("sender", "Unknown")
                content = item.get("content", "")
                status = item.get("status", "")
                
                # Wrap long content
                wrapped_content = wrap_text(content, 80)
                content_text = "<br/>".join(wrapped_content) if len(wrapped_content) > 1 else content
                
                story.append(Paragraph(f"<b>{timestamp_str}</b>", body_style))
                story.append(Paragraph(f"{direction_icon} <b>{sender}</b>: {content_text}", body_style))
                if status:
                    story.append(Paragraph(f"<i>Status: {status}</i>", body_style))
                
            elif item.get("type") == "audit":
                action = item.get("action", "")
                actor = item.get("actor", "System")
                payload = item.get("payload", {})
                details = item.get("details", "")
                
                story.append(Paragraph(f"<b>{timestamp_str}</b>", body_style))
                story.append(Paragraph(f"🔄 <b>{actor}</b> - {action}", body_style))
                
                # Add payload details if available
                if payload:
                    payload_text = ", ".join([f"{k}: {v}" for k, v in payload.items() if v])
                    if payload_text:
                        story.append(Paragraph(f"<i>Details: {payload_text}</i>", body_style))
                
                if details:
                    wrapped_details = wrap_text(details, 80)
                    details_text = "<br/>".join(wrapped_details)
                    story.append(Paragraph(f"<i>{details_text}</i>", body_style))
            
            story.append(Spacer(1, 8))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Generate filename based on export type
        export_type_label = export_type.replace("_", "-")
        filename = f"conversation-{conversation_id}-{export_type_label}-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf"
        
        logger.info(f"PDF export generated: {filename} by user {current_user.email}")
        
        return Response(
            buffer.read(), 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF export: {str(e)}")
        return Response("Error generating PDF export", status_code=500)


