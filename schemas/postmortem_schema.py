from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactScope(str, Enum):
    INTERNAL = "internal"
    CUSTOMER_FACING = "customer_facing"
    PARTIAL_OUTAGE = "partial_outage"
    FULL_OUTAGE = "full_outage"


class FailureType(str, Enum):
    DEPLOYMENT_ERROR = "deployment_error"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_FAILURE = "dependency_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    HUMAN_ERROR = "human_error"
    THIRD_PARTY_ISSUE = "third_party_issue"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    OTHER = "other"


class TimelineEvent(BaseModel):
    timestamp: datetime
    description: str
    event_type: str  # "detection", "response", "mitigation", "resolution"


class Impact(BaseModel):
    affected_services: List[str]
    user_impact: str
    duration_minutes: int
    scope: ImpactScope
    metrics: Optional[Dict[str, Any]] = None  # e.g., error rates, affected users


class RootCause(BaseModel):
    primary_cause: str
    technical_details: str
    failure_type: FailureType
    contributing_factors: List[str]


class RemediationAction(BaseModel):
    action: str
    category: str  # "technical", "process", "monitoring", "training"
    owner: Optional[str] = None
    status: Optional[str] = None  # "planned", "in_progress", "completed"


class FailurePattern(BaseModel):
    pattern_name: str
    description: str
    indicators: List[str]
    prevention_strategies: List[str]


class ExtractedPostmortem(BaseModel):
    title: str
    organization: str
    incident_date: datetime
    severity: SeverityLevel
    
    # Core failure analysis
    root_cause: RootCause
    impact: Impact
    timeline: List[TimelineEvent]
    
    # Learning and prevention
    remediation_actions: List[RemediationAction]
    detected_patterns: List[FailurePattern]
    
    # Metadata
    raw_text_hash: str  # For deduplication
    extraction_timestamp: datetime
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Free text fields for additional context
    summary: str
    lessons_learned: List[str]


class IngestionRequest(BaseModel):
    raw_text: str
    source_url: Optional[str] = None
    organization: Optional[str] = None
    incident_date: Optional[datetime] = None


class IngestionResponse(BaseModel):
    success: bool
    extracted_data: Optional[ExtractedPostmortem] = None
    error_message: Optional[str] = None
    processing_time_seconds: float
