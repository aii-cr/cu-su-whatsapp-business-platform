# NEW CODE
"""
Definición del estado del agente para LangGraph + contrato transaccional.
Incluye 'stage' para forzar el flujo: selection -> customer -> schedule -> booked -> emailed -> done.
"""

from __future__ import annotations
from typing import List, TypedDict, Optional, Any, Annotated, Literal, Dict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ContractSelection(TypedDict, total=False):
    plan_id: int
    plan_name: str
    base_price_crc: int
    iptv_count: int
    telefonia: bool
    extras_price_crc: int
    total_price_crc: int


class CustomerInfo(TypedDict, total=False):
    full_name: str
    identification_number: str
    email: str
    mobile_number: str


class BookingInfo(TypedDict, total=False):
    date: str
    time_slot: str
    reservation_id: Optional[str]
    confirmation_number: Optional[str]


class ConfirmationFlags(TypedDict, total=False):
    selection_confirmed: bool
    booking_confirmed: bool
    email_sent: bool


class ContractState(TypedDict, total=False):
    selection: ContractSelection
    customer: CustomerInfo
    booking: BookingInfo
    confirmations: ConfirmationFlags


Stage = Literal["idle", "selection", "customer", "schedule", "booked", "emailed", "done"]

class AgentState(TypedDict, total=False):
    """Estado completo del agente de WhatsApp."""
    messages: Annotated[List[AnyMessage], add_messages]
    conversation_id: str
    attempts: int
    target_language: str
    summary: Optional[str]
    stage: Stage
    contract: ContractState
    # Campo auxiliar para inyectar snapshot al prompt
    system_snapshot: Optional[str]