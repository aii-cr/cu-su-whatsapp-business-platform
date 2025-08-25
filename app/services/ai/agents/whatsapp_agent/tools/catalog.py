# NEW CODE
"""
Immutable catalog of plans and add-ons (I.V.I prices in CRC).
"""

from __future__ import annotations
from typing import Dict, Any, List
from langchain_core.tools import tool

_PLANS: Dict[int, Dict[str, Any]] = {
    1: {"name": "100/100 Mbps", "price_crc": 29500},
    2: {"name": "250/250 Mbps", "price_crc": 39500},
    3: {"name": "500/500 Mbps", "price_crc": 44500},
    4: {"name": "1/1 Gbps",  "price_crc": 49500},
}
_IPTV_PRICE = 4590
_TELEFONIA_PRICE = 3590

@tool("list_plans_catalog", return_direct=False)
def list_plans_catalog() -> str:
    """
    Returns the catalog of plans and add-ons (JSON string) for the LLM to read/verbalize.
    """
    data = {
        "plans": [{"id": pid, "name": p["name"], "price_crc": p["price_crc"]} for pid, p in _PLANS.items()],
        "addons": {
            "iptv": {"unit_price_crc": _IPTV_PRICE, "allowed_range": [0, 10]},
            "telefonia": {"unit_price_crc": _TELEFONIA_PRICE, "allowed_values": [0, 1]},
        },
        "notes": [
            "All plans include Wi-Fi equipment, firewall and 24/7 support.",
            "IPTV: ₡4,590 I.V.I per device (maximum 10).",
            "VoIP Telephony: ₡3,590 I.V.I.",
        ],
    }
    # Simple JSON string so the model can quote details exactly.
    import json
    return json.dumps(data, ensure_ascii=False)
