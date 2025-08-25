# NEW CODE
"""
Tool to send confirmation email in English.
"""

from __future__ import annotations
import json
from typing import Annotated, Optional
from langchain_core.tools import tool
from app.services.ai.agents.whatsapp_agent.services.email_client import email_client

_EMAIL_TEMPLATE = """\
Hi {full_name},

Your American Data Networks installation is confirmed.

Service:
- Plan: {plan_name}
- IPTV devices: {iptv_count}
- VoIP Phone: {telefonia}

Installation:
- Date: {date}
- Time: {time_slot}

Billing:
- First month pre-charge on installation day.
- Installation cost: $0
- Second month: FREE

Confirmation Number: {confirmation_number}

If you need any changes, just reply to this message.
Thanks for choosing American Data Networks!
"""

@tool("send_confirmation_email", return_direct=False)
async def send_confirmation_email(
    email: Annotated[str, "Destination email"],
    full_name: Annotated[str, "Customer full name"],
    plan_name: Annotated[str, "Plan name"],
    iptv_count: Annotated[int, "Number of IPTV devices"],
    telefonia: Annotated[bool, "Has VoIP phone"],
    date: Annotated[str, "YYYY-MM-DD"],
    time_slot: Annotated[str, "08:00 or 13:00"],
    confirmation_number: Annotated[str, "Booking confirmation number"],
) -> str:
    """
    Sends confirmation email in English. Returns JSON with ok: true/false.
    """
    body = _EMAIL_TEMPLATE.format(
        full_name=full_name,
        plan_name=plan_name,
        iptv_count=iptv_count,
        telefonia="Yes" if telefonia else "No",
        date=date,
        time_slot=time_slot,
        confirmation_number=confirmation_number,
    )
    ok = await email_client.send(to=email, subject="ADN Installation Confirmation", text=body)
    return json.dumps({"ok": ok}, ensure_ascii=False)
