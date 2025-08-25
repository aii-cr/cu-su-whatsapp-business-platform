# NEW CODE
"""
Deterministic quote calculation and selection validation (without advancing state).
"""

from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator
from app.services.ai.agents.whatsapp_agent.tools.catalog import _PLANS, _IPTV_PRICE, _TELEFONIA_PRICE

class QuoteInput(BaseModel):
    plan: Annotated[str, Field(description="Plan ID (1-4) or name ('1 Gbps', '500 Mbps', etc.)")]
    iptv_count: Annotated[int, Field(ge=0, le=10, description="IPTV quantity (0-10)")]
    telefonia: Annotated[bool, Field(description="True if includes VoIP Telephony")]

    @field_validator("plan")
    @classmethod
    def plan_non_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("plan required")
        return v

def _resolve_plan(plan_input: str) -> Optional[tuple[int, str, int]]:
    s = str(plan_input).strip().lower()
    # Try numeric id first
    try:
        pid = int(s)
        if pid in _PLANS:
            p = _PLANS[pid]
            return pid, p["name"], p["price_crc"]
    except Exception:
        pass
    # Try name match
    for pid, p in _PLANS.items():
        if p["name"].lower() == s or s in p["name"].lower():
            return pid, p["name"], p["price_crc"]
    return None

def _as_int_crc(d: Decimal) -> int:
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

@tool("quote_selection", return_direct=False)
def quote_selection(plan: str, iptv_count: int, telefonia: bool) -> str:
    """
    Validates selection and returns price breakdown in CRC (JSON string). Does not persist state.
    """
    from pydantic import ValidationError
    import json

    try:
        payload = QuoteInput(plan=plan, iptv_count=iptv_count, telefonia=telefonia)
    except ValidationError as ve:
        return json.dumps({"ok": False, "errors": ve.errors()}, ensure_ascii=False)

    resolved = _resolve_plan(payload.plan)
    if not resolved:
        return json.dumps({"ok": False, "errors": [{"loc": ["plan"], "msg": "Invalid plan", "type": "value_error"}]}, ensure_ascii=False)

    plan_id, plan_name, base_crc = resolved

    iptv_total = Decimal(_IPTV_PRICE) * Decimal(payload.iptv_count)
    tel_total = Decimal(_TELEFONIA_PRICE) if payload.telefonia else Decimal(0)
    total = Decimal(base_crc) + iptv_total + tel_total

    data = {
        "ok": True,
        "selection": {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "base_price_crc": base_crc,
            "iptv_count": payload.iptv_count,
            "telefonia": bool(payload.telefonia),
            "extras_price_crc": _as_int_crc(iptv_total + tel_total),
            "total_price_crc": _as_int_crc(total),
        },
        "policy": {
            "iptv_max": 10,
            "telefonia_max": 1
        }
    }
    return json.dumps(data, ensure_ascii=False)
