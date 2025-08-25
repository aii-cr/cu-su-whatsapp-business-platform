# NEW CODE
"""
Tools for installation slots and bookings (using services.http).
"""

from __future__ import annotations
from typing import Annotated, List, Dict, Any
import json
from datetime import datetime
from langchain_core.tools import tool
from app.services.ai.agents.whatsapp_agent.services.http import reservations_http


def _format_date_human(d: str) -> str:
    """Return 'Month DD, YYYY' robustly on Linux/Windows."""
    dt = datetime.strptime(d, "%Y-%m-%d")
    # Avoid %-d portability; strip leading zero manually
    day = str(int(dt.strftime("%d")))
    return f"{dt.strftime('%B')} {day}, {dt.strftime('%Y')}"


def _format_slots_whatsapp(closest_preview: Dict[str, List[str]]) -> str:
    """Build the exact WhatsApp text required for slot preview."""
    lines = []
    lines.append("Here are the available installation slots:\n")
    lines.append("Dates and Times:")
    for iso_day, times in closest_preview.items():
        human = _format_date_human(iso_day)
        # Sort/unique and print as "08:00, 13:00"
        tdisp = ", ".join(sorted(set(times)))
        lines.append(f"• {human}: {tdisp}")
    lines.append("\nPlease choose a date and a time slot (08:00 or 13:00) that works best for you! 📅")
    return "\n".join(lines)

@tool("get_available_slots", return_direct=False)
async def get_available_slots() -> str:
    """
    Gets available slots for the next 4 weeks.
    Returns JSON with:
      - ok: bool
      - available_slots: {YYYY-MM-DD: [HH:MM, ...]}
      - period: {...}
      - closest_preview: first 5 days for UX
      - whatsapp_text: preformatted message to send directly
    """
    status, data = await reservations_http.get_json("/available-slots")
    if status != 200:
        return json.dumps({"ok": False, "status": status, "error": "Failed to fetch slots"}, ensure_ascii=False)

    days = sorted(data.get("available_slots", {}).items(), key=lambda x: x[0])
    closest_preview = dict(days[:5]) if days else {}

    payload = {
        "ok": True,
        "available_slots": data.get("available_slots", {}),
        "period": data.get("period", {}),
        "closest_preview": closest_preview,
    }
    payload["whatsapp_text"] = _format_slots_whatsapp(closest_preview) if closest_preview else \
        "We couldn't find open slots right now. Please try again shortly."

    return json.dumps(payload, ensure_ascii=False)

@tool("book_installation", return_direct=False)
async def book_installation(
    date: Annotated[str, "YYYY-MM-DD"],
    time_slot: Annotated[str, "08:00 or 13:00"],
    full_name: Annotated[str, "Customer full name"],
    identification_number: Annotated[str, "ID/passport"],
    email: Annotated[str, "Valid email"],
    mobile_number: Annotated[str, "CR phone +506########"],
    service_type: Annotated[str, "Defaults to 'fiber_installation'"] = "fiber_installation",
) -> str:
    """
    Books an installation if the slot is still available. Returns JSON with confirmation data or frontend-friendly error.
    """
    payload = {
        "date": date,
        "time_slot": time_slot,
        "customer_info": {
            "full_name": full_name,
            "identification_number": identification_number,
            "email": email,
            "mobile_number": mobile_number,
        },
        "service_type": service_type,
    }
    status, data = await reservations_http.post_json("/book", payload)
    if status != 200 or not data.get("success"):
        # Normalize 409/422/500 errors into a common format
        err = {
            "ok": False,
            "status": status,
            "error_code": data.get("error_code") or "BOOK_ERROR",
            "error_message": data.get("error_message") or "Failed to book",
            "details": data.get("details"),
        }
        return json.dumps(err, ensure_ascii=False)

    return json.dumps({"ok": True, "booking": data["data"]}, ensure_ascii=False)
