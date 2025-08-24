# NEW CODE
"""
Herramientas para slots y reservas de instalación (usando services.http).
"""

from __future__ import annotations
from typing import Annotated, List, Dict, Any
import json
from langchain_core.tools import tool
from app.services.ai.agents.whatsapp_agent.services.http import reservations_http

@tool("get_available_slots", return_direct=False)
async def get_available_slots() -> str:
    """
    Obtiene slots disponibles para las próximas 4 semanas. Devuelve JSON con 'available_slots' y 'period'.
    """
    status, data = await reservations_http.get_json("/available-slots")
    if status != 200:
        return json.dumps({"ok": False, "status": status, "error": "Failed to fetch slots"}, ensure_ascii=False)

    # Reordenar fechas por cercanía (aunque backend ya viene ordenado)
    days = sorted(data.get("available_slots", {}).items(), key=lambda x: x[0])
    closest_preview = days[:5]  # cortesía para el LLM al momento de ofrecer
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
    Reserva una instalación si el slot sigue libre. Devuelve JSON con datos de confirmación o error frontend-friendly.
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
        # Normalizar errores 409/422/500 en un formato común
        err = {
            "ok": False,
            "status": status,
            "error_code": data.get("error_code") or "BOOK_ERROR",
            "error_message": data.get("error_message") or "Failed to book",
            "details": data.get("details"),
        }
        return json.dumps(err, ensure_ascii=False)

    return json.dumps({"ok": True, "booking": data["data"]}, ensure_ascii=False)
