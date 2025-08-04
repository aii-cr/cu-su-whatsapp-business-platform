"""Business and organizational schemas package."""

from .department import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentDetailResponse,
    DepartmentListResponse, DepartmentQueryParams, BusinessHoursConfig, SLASettings,
    AgentAssignment, AgentRemoval, DepartmentStatsResponse, DepartmentPerformance,
    DepartmentWorkload, RoutingRule
)

from .company_profile import (
    CompanyProfileUpdate, CompanyProfileResponse, BrandingConfig, FeatureConfig,
    IntegrationSettings, ComplianceSettings, NotificationPreferences,
    CompanyStatsResponse, UsageLimits, SubscriptionInfo, CompanyBackup
)

__all__ = [
    # Department schemas
    "DepartmentCreate", "DepartmentUpdate", "DepartmentResponse", "DepartmentDetailResponse",
    "DepartmentListResponse", "DepartmentQueryParams", "BusinessHoursConfig", "SLASettings",
    "AgentAssignment", "AgentRemoval", "DepartmentStatsResponse", "DepartmentPerformance",
    "DepartmentWorkload", "RoutingRule",
    
    # Company profile schemas
    "CompanyProfileUpdate", "CompanyProfileResponse", "BrandingConfig", "FeatureConfig",
    "IntegrationSettings", "ComplianceSettings", "NotificationPreferences",
    "CompanyStatsResponse", "UsageLimits", "SubscriptionInfo", "CompanyBackup"
] 