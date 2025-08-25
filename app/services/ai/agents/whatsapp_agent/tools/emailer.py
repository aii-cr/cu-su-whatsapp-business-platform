"""
Tools to send confirmation emails and generate confirmation numbers.
"""

from __future__ import annotations
import json
import re
from typing import Annotated, Optional
from langchain_core.tools import tool
from app.services.ai.agents.whatsapp_agent.services.email_client import email_client
from app.services.ai.agents.whatsapp_agent.templates.email_templates import (
    CONFIRMATION_EMAIL_HTML,
    CONFIRMATION_EMAIL_TEXT
)
from app.core.logger import logger


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date_format(date: str) -> bool:
    """Validate date format YYYY-MM-DD."""
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date))


def validate_time_slot(time_slot: str) -> bool:
    """Validate time slot format."""
    valid_slots = ["08:00", "13:00"]
    return time_slot in valid_slots


@tool("generate_confirmation_number", return_direct=False)
async def generate_confirmation_number() -> str:
    """
    Generate a unique confirmation number for booking confirmations.
    
    Returns:
        JSON string with the generated confirmation number
    """
    try:
        confirmation_number = email_client.generate_confirmation_number()
        logger.info(f"Generated confirmation number: {confirmation_number}")
        return json.dumps({
            "ok": True,
            "confirmation_number": confirmation_number
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error generating confirmation number: {e}")
        return json.dumps({
            "ok": False,
            "error": f"Failed to generate confirmation number: {str(e)}"
        }, ensure_ascii=False)


@tool("send_confirmation_email", return_direct=False)
async def send_confirmation_email(
    email: Annotated[str, "Destination email address"],
    full_name: Annotated[str, "Customer full name"],
    plan_name: Annotated[str, "Plan name"],
    iptv_count: Annotated[int, "Number of IPTV devices"],
    telefonia: Annotated[bool, "Has VoIP phone"],
    date: Annotated[str, "Installation date in YYYY-MM-DD format"],
    time_slot: Annotated[str, "Installation time slot: 08:00 or 13:00"],
    confirmation_number: Annotated[str, "Booking confirmation number"],
) -> str:
    """
    Sends confirmation email in English for American Data Networks installation.
    
    Args:
        email: Valid email address
        full_name: Customer's full name
        plan_name: Selected plan name
        iptv_count: Number of IPTV devices
        telefonia: Whether customer has VoIP phone
        date: Installation date (YYYY-MM-DD)
        time_slot: Installation time (08:00 or 13:00)
        confirmation_number: Unique confirmation number
        
    Returns:
        JSON string with success status and message
    """
    try:
        # Validate inputs
        if not validate_email(email):
            return json.dumps({
                "ok": False, 
                "error": "Invalid email format"
            }, ensure_ascii=False)
        
        if not validate_date_format(date):
            return json.dumps({
                "ok": False, 
                "error": "Invalid date format. Use YYYY-MM-DD"
            }, ensure_ascii=False)
        
        if not validate_time_slot(time_slot):
            return json.dumps({
                "ok": False, 
                "error": "Invalid time slot. Use 08:00 or 13:00"
            }, ensure_ascii=False)
        
        if not full_name.strip():
            return json.dumps({
                "ok": False, 
                "error": "Full name cannot be empty"
            }, ensure_ascii=False)
        
        if not plan_name.strip():
            return json.dumps({
                "ok": False, 
                "error": "Plan name cannot be empty"
            }, ensure_ascii=False)
        
        if iptv_count < 0:
            return json.dumps({
                "ok": False, 
                "error": "IPTV count cannot be negative"
            }, ensure_ascii=False)
        
        if not confirmation_number.strip():
            return json.dumps({
                "ok": False, 
                "error": "Confirmation number cannot be empty"
            }, ensure_ascii=False)
        
        # Format data for template
        telefonia_text = "Yes" if telefonia else "No"
        
        # Format date for display (convert YYYY-MM-DD to readable format)
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except:
            formatted_date = date
        
        # Send HTML email using the enhanced template
        logger.info(f"Sending confirmation email to {email} for {full_name}")
        
        # Try HTML email first
        success = await email_client.send_html_email(
            to=email,
            subject="American Data Networks | Installation Confirmation",
            html_content=CONFIRMATION_EMAIL_HTML.format(
                full_name=full_name.strip(),
                plan_name=plan_name.strip(),
                iptv_count=iptv_count,
                telefonia=telefonia_text,
                date=formatted_date,
                time_slot=time_slot,
                confirmation_number=confirmation_number.strip(),
            )
        )
        
        # If HTML fails, try text-only as fallback
        if not success:
            logger.warning(f"HTML email failed, trying text-only fallback for {email}")
            text_content = CONFIRMATION_EMAIL_TEXT.format(
                full_name=full_name.strip(),
                plan_name=plan_name.strip(),
                iptv_count=iptv_count,
                telefonia=telefonia_text,
                date=formatted_date,
                time_slot=time_slot,
                confirmation_number=confirmation_number.strip(),
            )
            
            success = await email_client.send(
                to=email,
                subject="American Data Networks | Installation Confirmation",
                text=text_content
            )
        
        if success:
            logger.info(f"Confirmation email sent successfully to {email}")
            return json.dumps({
                "ok": True,
                "message": f"Confirmation email sent successfully to {email}",
                "confirmation_number": confirmation_number
            }, ensure_ascii=False)
        else:
            logger.error(f"Failed to send confirmation email to {email}")
            return json.dumps({
                "ok": False,
                "error": "Failed to send email. Please try again later."
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error in send_confirmation_email: {e}")
        return json.dumps({
            "ok": False,
            "error": f"Internal error: {str(e)}"
        }, ensure_ascii=False)


@tool("send_confirmation_email_with_auto_number", return_direct=False)
async def send_confirmation_email_with_auto_number(
    email: Annotated[str, "Destination email address"],
    full_name: Annotated[str, "Customer full name"],
    plan_name: Annotated[str, "Plan name"],
    iptv_count: Annotated[int, "Number of IPTV devices"],
    telefonia: Annotated[bool, "Has VoIP phone"],
    date: Annotated[str, "Installation date in YYYY-MM-DD format"],
    time_slot: Annotated[str, "Installation time slot: 08:00 or 13:00"],
) -> str:
    """
    Sends confirmation email with automatically generated confirmation number.
    
    Args:
        email: Valid email address
        full_name: Customer's full name
        plan_name: Selected plan name
        iptv_count: Number of IPTV devices
        telefonia: Whether customer has VoIP phone
        date: Installation date (YYYY-MM-DD)
        time_slot: Installation time (08:00 or 13:00)
        
    Returns:
        JSON string with success status, message, and generated confirmation number
    """
    try:
        # Generate confirmation number
        confirmation_number = email_client.generate_confirmation_number()
        
        # Use the main send_confirmation_email function
        result = await send_confirmation_email(
            email=email,
            full_name=full_name,
            plan_name=plan_name,
            iptv_count=iptv_count,
            telefonia=telefonia,
            date=date,
            time_slot=time_slot,
            confirmation_number=confirmation_number
        )
        
        # Parse the result and add the confirmation number
        result_dict = json.loads(result)
        if result_dict.get("ok"):
            result_dict["confirmation_number"] = confirmation_number
            result_dict["message"] = f"Confirmation email sent successfully to {email} with confirmation number {confirmation_number}"
        
        return json.dumps(result_dict, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in send_confirmation_email_with_auto_number: {e}")
        return json.dumps({
            "ok": False,
            "error": f"Internal error: {str(e)}"
        }, ensure_ascii=False)
