# NEW CODE
"""
Toolbelt del agente: RAG + herramientas transaccionales.
"""

from __future__ import annotations
from typing import List, Any

# RAG (tu herramienta existente)
from app.services.ai.shared.tools.rag.retriever import retrieve_information as adn_retrieve

# Herramientas nuevas
from app.services.ai.agents.whatsapp_agent.tools.pricing import quote_selection
from app.services.ai.agents.whatsapp_agent.tools.validators import validate_customer_info
from app.services.ai.agents.whatsapp_agent.tools.reservations import get_available_slots, book_installation
from app.services.ai.agents.whatsapp_agent.tools.emailer import send_confirmation_email
from app.services.ai.agents.whatsapp_agent.tools.catalog import list_plans_catalog


def get_tool_belt() -> List[Any]:
    """Lista de herramientas disponibles para bind_tools."""
    return [
        adn_retrieve,              # RAG
        list_plans_catalog,        # Catálogo planes
        quote_selection,           # Cotización/validación selección
        validate_customer_info,    # Validación datos cliente
        get_available_slots,       # Slots disponibles
        book_installation,         # Reservar instalación
        send_confirmation_email,   # Enviar correo confirmación
    ]
