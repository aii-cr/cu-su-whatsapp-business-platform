# NEW CODE
"""
Tools for installation slots and bookings (using services.http).
"""

from __future__ import annotations
from typing import Annotated, List, Dict, Any
import json
from langchain_core.tools import tool
from app.services.ai.agents.whatsapp_agent.services.http import reservations_http

@tool("get_available_slots", return_direct=False)
async def get_available_slots() -> str:
    """
    Gets available slots for the next 4 weeks. Returns JSON with 'available_slots' and 'period'.
    """
    status, data = await reservations_http.get_json("/available-slots")
    if status != 200:
        return json.dumps({"ok": False, "status": status, "error": "Failed to fetch slots"}, ensure_ascii=False)

    # Reorder dates by proximity (although backend already comes ordered)
    days = sorted(data.get("available_slots", {}).items(), key=lambda x: x[0])
    closest_preview = days[:5]  # courtesy for the LLM when offering
    data["closest_preview"] = dict(closest_preview)
    data["ok"] = True
    return json.dumps(data, ensure_ascii=False)

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
