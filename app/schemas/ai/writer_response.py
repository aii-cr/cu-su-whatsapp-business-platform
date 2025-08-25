"""
Pydantic schemas for Writer Agent structured responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class StructuredWriterResponse(BaseModel):
    """Structured response from Writer Agent with separate customer response and reasoning."""
    
    customer_response: str = Field(
        ...,
        description="The actual message text to send to the customer, preserving WhatsApp formatting"
    )
    reason: str = Field(
        ..., 
        description="Brief explanation of reasoning, strategy, and tips for this response approach"
    )


class WriterAgentResult(BaseModel):
    """Complete Writer Agent result with structured response and metadata."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    structured_response: Optional[StructuredWriterResponse] = Field(
        None, 
        description="Parsed structured response with customer_response and reason"
    )
    raw_response: str = Field("", description="Raw response from the AI model")
    metadata: dict = Field(default_factory=dict, description="Processing metadata")
    error: Optional[str] = Field(None, description="Error message if failed")
