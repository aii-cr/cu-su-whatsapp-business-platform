# NEW CODE
"""
Customer data validation. Returns normalized payload + errors by field.
"""

from __future__ import annotations
import re
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr, field_validator
from langchain_core.tools import tool
import json

_CR_PHONE = re.compile(r"^(?:\+?506)?[ -]?(\d{4})[ -]?(\d{4})$")

class CustomerInput(BaseModel):
    full_name: Annotated[str, Field(min_length=2, max_length=100)]
    identification_number: Annotated[str, Field(min_length=5, max_length=50)]
    email: EmailStr
    mobile_number: Annotated[str, Field(min_length=8, max_length=20)]

    @field_validator("identification_number")
    @classmethod
    def id_chars(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9\-]+", v):
            raise ValueError("Only alphanumeric and hyphens")
        return v

    @field_validator("mobile_number")
    @classmethod
    def cr_mobile(cls, v: str) -> str:
        v = v.strip()
        m = _CR_PHONE.match(v)
        if not m:
            raise ValueError("Invalid format, e.g: +506 8888 8888")
        # Normalize to international +506########
        digits = "".join(m.groups())
        return f"+506{digits}"

@tool("validate_customer_info", return_direct=False)
def validate_customer_info(full_name: str, identification_number: str, email: str, mobile_number: str) -> str:
    """
    Validates and normalizes customer information. Returns JSON with ok/errors and payload.
    """
    from pydantic import ValidationError
    try:
        data = CustomerInput(
            full_name=full_name,
            identification_number=identification_number,
            email=email,
            mobile_number=mobile_number,
        )
        return json.dumps({"ok": True, "customer": data.model_dump()}, ensure_ascii=False)
    except ValidationError as ve:
        return json.dumps({"ok": False, "errors": ve.errors()}, ensure_ascii=False)
