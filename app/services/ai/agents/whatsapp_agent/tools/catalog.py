# NEW CODE
"""
Catálogo inmutable de planes y adicionales (precios I.V.I en CRC).
"""

from __future__ import annotations
from typing import Dict, Any, List
from langchain_core.tools import tool

_PLANS: Dict[int, Dict[str, Any]] = {
    1: {"name": "100 Mbps", "price_crc": 29500},
    2: {"name": "250 Mbps", "price_crc": 39500},
    3: {"name": "500 Mbps", "price_crc": 44500},
    4: {"name": "1 Gbps",  "price_crc": 49500},
}
_IPTV_PRICE = 4590
_TELEFONIA_PRICE = 3590

@tool("list_plans_catalog", return_direct=False)
def list_plans_catalog() -> str:
    """
    Devuelve el catálogo de planes y adicionales (JSON string) para que el LLM lo lea/verbalice.
    """
    data = {
        "plans": [{"id": pid, "name": p["name"], "price_crc": p["price_crc"]} for pid, p in _PLANS.items()],
        "addons": {
            "iptv": {"unit_price_crc": _IPTV_PRICE, "allowed_range": [0, 10]},
            "telefonia": {"unit_price_crc": _TELEFONIA_PRICE, "allowed_values": [0, 1]},
        },
        "notes": [
            "Todos los planes incluyen equipo Wi-Fi, firewall y soporte 24/7.",
            "IPTV: ₡4.590 I.V.I por dispositivo (máximo 10).",
            "Telefonía VoIP: ₡3.590 I.V.I (máximo 1).",
        ],
    }
    # Simple JSON string so the model can quote details exactly.
    import json
    return json.dumps(data, ensure_ascii=False)
