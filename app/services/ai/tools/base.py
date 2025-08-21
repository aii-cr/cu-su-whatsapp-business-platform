"""
Base tool class with common functionality for all agent tools.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

from app.core.logger import logger


class ToolResult(BaseModel):
    """Standard result format for all tools."""
    status: str = Field(..., description="Tool execution status (success/error/timeout)")
    data: Any = Field(default=None, description="Tool result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    trace_id: str = Field(..., description="Unique trace identifier")
    execution_time_ms: int = Field(..., description="Tool execution time in milliseconds")
    tool_name: str = Field(..., description="Name of the tool that was executed")
    
    
class BaseTool(ABC):
    """
    Base class for all agent tools.
    Provides common functionality like error handling, timeouts, and tracing.
    """
    
    def __init__(self, name: str, description: str, timeout_seconds: int = 8):
        self.name = name
        self.description = description
        self.timeout_seconds = timeout_seconds
        
    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        """
        Implement the actual tool logic here.
        This method should contain the core tool functionality.
        """
        pass
    
    async def execute_with_timeout(self, **kwargs) -> ToolResult:
        """
        Execute tool with timeout and error handling.
        
        Args:
            **kwargs: Tool-specific arguments
            
        Returns:
            ToolResult with execution details
        """
        trace_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Executing tool {self.name} with trace_id: {trace_id}")
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute(**kwargs),
                timeout=self.timeout_seconds
            )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Tool {self.name} completed successfully (trace_id: {trace_id})")
            
            return ToolResult(
                status="success",
                data=result,
                trace_id=trace_id,
                execution_time_ms=int(execution_time),
                tool_name=self.name
            )
            
        except asyncio.TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Tool {self.name} timed out after {self.timeout_seconds}s"
            
            logger.warning(f"{error_msg} (trace_id: {trace_id})")
            
            return ToolResult(
                status="timeout",
                error=error_msg,
                trace_id=trace_id,
                execution_time_ms=int(execution_time),
                tool_name=self.name
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Tool {self.name} failed: {str(e)}"
            
            logger.error(f"{error_msg} (trace_id: {trace_id})")
            
            return ToolResult(
                status="error",
                error=error_msg,
                trace_id=trace_id,
                execution_time_ms=int(execution_time),
                tool_name=self.name
            )
    
    def to_structured_tool(self, input_schema: BaseModel) -> StructuredTool:
        """
        Convert to LangChain StructuredTool.
        
        Args:
            input_schema: Pydantic model defining tool inputs
            
        Returns:
            StructuredTool instance
        """
        async def tool_wrapper(**kwargs) -> Dict[str, Any]:
            """Wrapper function for the StructuredTool."""
            result = await self.execute_with_timeout(**kwargs)
            return result.model_dump()
        
        return StructuredTool(
            name=self.name,
            description=self.description,
            args_schema=input_schema,
            func=tool_wrapper,
            coroutine=tool_wrapper
        )
