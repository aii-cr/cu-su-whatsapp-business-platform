"""
Base model and utilities for database models.
"""
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing import Annotated, Any
from bson import ObjectId
import pydantic
import pydantic_core
import pydantic_core.core_schema as core_schema

class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic v2 compatibility."""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v),
                return_schema=core_schema.str_schema()
            )
        )

    @classmethod
    def _validate(cls, v: Any) -> ObjectId:
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {"type": "string", "format": "objectid", "examples": ["507f1f77bcf86cd799439011"]}

# Type annotation for ObjectId fields
ObjectIdField = Annotated[PyObjectId, PyObjectId] 