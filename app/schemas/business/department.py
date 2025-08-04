"""Department-related request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from app.db.models.base import PyObjectId

# Department Creation
class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Department name")
    description: Optional[str] = Field(None, max_length=500, description="Department description")
    email: Optional[str] = Field(None, description="Department email")
    phone: Optional[str] = Field(None, description="Department phone")
    timezone: str = Field("UTC", description="Department timezone")
    business_hours: Dict[str, Any] = Field(default={}, description="Business hours configuration")
    sla_settings: Dict[str, Any] = Field(default={}, description="SLA settings")
    routing_settings: Dict[str, Any] = Field(default={}, description="Routing settings")
    auto_assignment_enabled: bool = Field(True, description="Enable auto-assignment")
    max_conversations_per_agent: int = Field(10, ge=1, description="Max conversations per agent")
    tags: List[str] = Field(default=[], description="Department tags")

# Department Update
class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated department name")
    description: Optional[str] = Field(None, max_length=500, description="Updated department description")
    email: Optional[str] = Field(None, description="Updated department email")
    phone: Optional[str] = Field(None, description="Updated department phone")
    timezone: Optional[str] = Field(None, description="Updated department timezone")
    business_hours: Optional[Dict[str, Any]] = Field(None, description="Updated business hours")
    sla_settings: Optional[Dict[str, Any]] = Field(None, description="Updated SLA settings")
    routing_settings: Optional[Dict[str, Any]] = Field(None, description="Updated routing settings")
    auto_assignment_enabled: Optional[bool] = Field(None, description="Updated auto-assignment setting")
    max_conversations_per_agent: Optional[int] = Field(None, ge=1, description="Updated max conversations per agent")
    tags: Optional[List[str]] = Field(None, description="Updated department tags")
    is_active: Optional[bool] = Field(None, description="Updated active status")

# Department Response
class DepartmentResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: str
    status: str
    business_hours: Dict[str, Any] = {}
    sla_settings: Dict[str, Any] = {}
    routing_settings: Dict[str, Any] = {}
    auto_assignment_enabled: bool
    max_conversations_per_agent: int
    is_active: bool
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    agent_count: int = 0
    active_conversations: int = 0

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Department with Statistics Response
class DepartmentDetailResponse(DepartmentResponse):
    agents: List[Dict[str, Any]] = []
    conversation_stats: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}

# Department List Response
class DepartmentListResponse(BaseModel):
    departments: List[DepartmentResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Department Query Parameters
class DepartmentQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search in department name or description")
    status: Optional[str] = Field(None, description="Filter by status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    timezone: Optional[str] = Field(None, description="Filter by timezone")
    has_agents: Optional[bool] = Field(None, description="Filter departments with agents")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

# Business Hours Configuration
class BusinessHoursConfig(BaseModel):
    monday: Dict[str, Any] = Field(default={"enabled": True, "start": "09:00", "end": "17:00"})
    tuesday: Dict[str, Any] = Field(default={"enabled": True, "start": "09:00", "end": "17:00"})
    wednesday: Dict[str, Any] = Field(default={"enabled": True, "start": "09:00", "end": "17:00"})
    thursday: Dict[str, Any] = Field(default={"enabled": True, "start": "09:00", "end": "17:00"})
    friday: Dict[str, Any] = Field(default={"enabled": True, "start": "09:00", "end": "17:00"})
    saturday: Dict[str, Any] = Field(default={"enabled": False, "start": "09:00", "end": "17:00"})
    sunday: Dict[str, Any] = Field(default={"enabled": False, "start": "09:00", "end": "17:00"})
    holidays: List[str] = Field(default=[], description="Holiday dates (YYYY-MM-DD)")

# SLA Settings Configuration
class SLASettings(BaseModel):
    first_response_time_minutes: int = Field(60, ge=1, description="First response SLA in minutes")
    resolution_time_hours: int = Field(24, ge=1, description="Resolution SLA in hours")
    escalation_enabled: bool = Field(True, description="Enable escalation")
    escalation_time_minutes: int = Field(120, ge=1, description="Escalation time in minutes")
    priority_multipliers: Dict[str, float] = Field(
        default={"low": 1.5, "normal": 1.0, "high": 0.5, "urgent": 0.25},
        description="SLA multipliers by priority"
    )

# Agent Assignment
class AgentAssignment(BaseModel):
    department_id: PyObjectId = Field(..., description="Department ID")
    agent_id: PyObjectId = Field(..., description="Agent ID to assign")
    role: str = Field("agent", pattern="^(agent|supervisor|manager)$", description="Agent role in department")

# Agent Removal
class AgentRemoval(BaseModel):
    department_id: PyObjectId = Field(..., description="Department ID")
    agent_id: PyObjectId = Field(..., description="Agent ID to remove")

# Department Statistics
class DepartmentStatsResponse(BaseModel):
    total_departments: int
    active_departments: int
    departments_by_status: Dict[str, int]
    total_agents: int
    agents_by_department: Dict[str, int]
    conversation_distribution: Dict[str, int]
    average_response_time_by_department: Dict[str, float]

# Department Performance
class DepartmentPerformance(BaseModel):
    department_id: PyObjectId
    department_name: str
    period_start: datetime
    period_end: datetime
    metrics: Dict[str, Any]
    sla_compliance: Dict[str, float]
    agent_performance: List[Dict[str, Any]]

# Department Workload
class DepartmentWorkload(BaseModel):
    department_id: PyObjectId
    department_name: str
    active_agents: int
    total_conversations: int
    unassigned_conversations: int
    average_conversations_per_agent: float
    workload_percentage: float
    status: str  # normal, busy, overloaded

# Routing Rule
class RoutingRule(BaseModel):
    department_id: PyObjectId = Field(..., description="Department ID")
    conditions: List[Dict[str, Any]] = Field(..., description="Routing conditions")
    priority: int = Field(1, ge=1, le=10, description="Rule priority")
    is_active: bool = Field(True, description="Whether rule is active") 