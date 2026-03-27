"""
SOC Alert Triage Environment - Models
OpenEnv Hackathon Submission - Meta PyTorch 2026
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskDifficulty(str, Enum):
    """Task difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AlertSeverity(str, Enum):
    """Alert severity classifications."""
    FALSE_POSITIVE = "false_positive"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertSource(str, Enum):
    """Sources of security alerts."""
    FIREWALL = "firewall"
    IDS = "ids"
    ENDPOINT = "endpoint"
    CLOUD = "cloud"
    EMAIL = "email"


class AttackStage(str, Enum):
    """MITRE ATT&CK stages."""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class SecurityAlert(BaseModel):
    """A single security alert."""
    alert_id: str = Field(..., description="Unique alert identifier")
    timestamp: int = Field(..., description="Unix timestamp")
    source: AlertSource = Field(..., description="Alert source system")
    alert_type: str = Field(..., description="Type of alert (e.g., 'malware_detected')")
    severity: AlertSeverity = Field(..., description="Alert severity")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    dest_ip: Optional[str] = Field(None, description="Destination IP address")
    user: Optional[str] = Field(None, description="Associated user")
    asset: Optional[str] = Field(None, description="Affected asset/hostname")
    description: str = Field(..., description="Alert description")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Additional alert data")
    ground_truth: Optional[AlertSeverity] = Field(None, description="True classification (for grader)")
    incident_id: Optional[str] = Field(None, description="True incident grouping (for grader)")


class Incident(BaseModel):
    """A correlated security incident."""
    incident_id: str = Field(..., description="Unique incident identifier")
    alerts: List[str] = Field(default_factory=list, description="Alert IDs in this incident")
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    affected_assets: List[str] = Field(default_factory=list, description="Assets affected")
    attack_stage: Optional[AttackStage] = Field(None, description="Current attack stage")
    confidence: float = Field(0.0, description="Confidence score 0.0-1.0")


class Campaign(BaseModel):
    """An Advanced Persistent Threat campaign."""
    campaign_id: str = Field(..., description="Campaign identifier")
    incidents: List[str] = Field(default_factory=list, description="Incident IDs")
    start_time: int = Field(..., description="Campaign start timestamp")
    end_time: Optional[int] = Field(None, description="Campaign end timestamp")
    attack_stages: List[AttackStage] = Field(default_factory=list, description="Stages observed")
    affected_assets: List[str] = Field(default_factory=list, description="All affected assets")


class TriageActionType(str, Enum):
    """Types of triage actions."""
    # Easy task actions
    CLASSIFY_ALERT = "classify_alert"

    # Medium task actions
    CREATE_INCIDENT = "create_incident"
    ADD_TO_INCIDENT = "add_to_incident"
    SET_ROOT_CAUSE = "set_root_cause"

    # Hard task actions
    INVESTIGATE = "investigate"
    ESCALATE = "escalate"
    REPORT_CAMPAIGN = "report_campaign"
    SET_RESPONSE = "set_response"


class ResponseAction(str, Enum):
    """Response actions for threats."""
    MONITOR = "monitor"
    CONTAIN = "contain"
    ISOLATE = "isolate"
    BLOCK = "block"
    ERADICATE = "eradicate"
    RECOVER = "recover"


class TriageAction(BaseModel):
    """Action model for SOC triage."""
    action_type: TriageActionType = Field(..., description="Type of action")
    alert_id: Optional[str] = Field(None, description="Target alert ID")
    incident_id: Optional[str] = Field(None, description="Target incident ID")
    classification: Optional[AlertSeverity] = Field(None, description="Classification (for classify)")
    root_cause: Optional[str] = Field(None, description="Root cause (for set_root_cause)")
    investigation_query: Optional[str] = Field(None, description="Query for investigation")
    response_action: Optional[ResponseAction] = Field(None, description="Response to take")
    campaign_id: Optional[str] = Field(None, description="Campaign ID for reporting")
    confidence: float = Field(0.5, description="Confidence 0.0-1.0")


class TriageObservation(BaseModel):
    """Observation model for SOC triage."""
    alerts: List[SecurityAlert] = Field(default_factory=list, description="Current alerts")
    incidents: List[Incident] = Field(default_factory=list, description="Current incidents")
    campaigns: List[Campaign] = Field(default_factory=list, description="Identified campaigns")
    investigation_results: Optional[Dict[str, Any]] = Field(None, description="Investigation output")
    message: str = Field("", description="Status message")
    done: bool = Field(False, description="Episode complete")
    reward: float = Field(0.0, description="Step reward")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")


class TriageState(BaseModel):
    """Environment state."""
    episode_id: str = Field(..., description="Unique episode ID")
    step_count: int = Field(default=0, description="Steps taken")
    task_difficulty: TaskDifficulty = Field(default=TaskDifficulty.EASY)
    total_alerts: int = Field(default=0, description="Total alerts processed")
    alerts_classified: int = Field(default=0, description="Alerts classified")
    incidents_created: int = Field(default=0, description="Incidents created")
    campaigns_reported: int = Field(default=0, description="Campaigns reported")
    current_score: float = Field(default=0.0, description="Current grader score")
    actions_history: List[Dict[str, Any]] = Field(default_factory=list, description="Action history")


class TaskConfig(BaseModel):
    """Configuration for a task."""
    max_steps: int = Field(..., description="Maximum steps per episode")
    num_alerts: int = Field(..., description="Number of alerts")
    false_positive_rate: float = Field(0.5, description="FP rate")
    noise_level: float = Field(0.0, description="Alert noise level")
    time_span_days: int = Field(1, description="Simulated time span")
    require_correlation: bool = Field(False, description="Require alert correlation")
    require_campaign_detection: bool = Field(False, description="Require campaign detection")
