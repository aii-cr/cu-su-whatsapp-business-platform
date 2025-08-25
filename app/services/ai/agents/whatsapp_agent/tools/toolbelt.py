# NEW CODE
"""
Agent toolbelt: RAG + transactional tools.
"""

from __future__ import annotations
from typing import List, Any

# RAG (your existing tool)
from app.services.ai.shared.tools.rag.retriever import retrieve_information as adn_retrieve

# New tools
from app.services.ai.agents.whatsapp_agent.tools.pricing import quote_selection
from app.services.ai.agents.whatsapp_agent.tools.validators import validate_customer_info
from app.services.ai.agents.whatsapp_agent.tools.reservations import get_available_slots, book_installation
from app.services.ai.agents.whatsapp_agent.tools.emailer import send_confirmation_email
from app.services.ai.agents.whatsapp_agent.tools.catalog import list_plans_catalog


def get_tool_belt() -> List[Any]:
    """List of available tools for bind_tools."""
    return [
        adn_retrieve,              # RAG
        list_plans_catalog,        # Plans catalog
        quote_selection,           # Quote/validate selection
        validate_customer_info,    # Validate customer data
        get_available_slots,       # Available slots
        book_installation,         # Book installation
        send_confirmation_email,   # Send confirmation email
    ]
