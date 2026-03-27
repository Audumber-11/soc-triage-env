"""Typed models for the IT Support OpenEnv environment."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import json


class TicketPriority(Enum):
    """Priority levels for IT support tickets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(Enum):
    """Status of a support ticket."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActionType(Enum):
    """Types of actions an agent can take."""
    # Information gathering
    VIEW_TICKET = "view_ticket"
    SEARCH_KNOWLEDGE_BASE = "search_knowledge_base"
    CHECK_SYSTEM_STATUS = "check_system_status"

    # Resolution actions
    ASSIGN_TICKET = "assign_ticket"
    ADD_COMMENT = "add_comment"
    APPLY_FIX = "apply_fix"
    ESCALATE = "escalate"

    # Communication
    NOTIFY_USER = "notify_user"
    REQUEST_INFO = "request_info"

    # Terminal
    RESOLVE = "resolve"
    CLOSE = "close"


@dataclass
class Ticket:
    """Represents an IT support ticket."""
    id: str
    title: str
    description: str
    category: str  # e.g., "network", "software", "hardware", "access"
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    requester: str
    assigned_to: Optional[str] = None
    comments: List[Dict[str, Any]] = field(default_factory=list)
    resolution_attempts: int = 0
    escalation_level: int = 0
    required_fixes: Set[str] = field(default_factory=set)
    applied_fixes: Set[str] = field(default_factory=set)
    time_spent_minutes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert ticket to dictionary for state serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "requester": self.requester,
            "assigned_to": self.assigned_to,
            "comments": self.comments,
            "resolution_attempts": self.resolution_attempts,
            "escalation_level": self.escalation_level,
            "time_spent_minutes": self.time_spent_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticket":
        """Create ticket from dictionary."""
        ticket = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            category=data["category"],
            priority=TicketPriority(data["priority"]),
            status=TicketStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            requester=data["requester"],
            assigned_to=data.get("assigned_to"),
        )
        ticket.comments = data.get("comments", [])
        ticket.resolution_attempts = data.get("resolution_attempts", 0)
        ticket.escalation_level = data.get("escalation_level", 0)
        ticket.time_spent_minutes = data.get("time_spent_minutes", 0)
        return ticket


@dataclass
class AgentAction:
    """Represents an action taken by the agent."""
    action_type: ActionType
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "params": self.params,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentAction":
        return cls(
            action_type=ActionType(data["action_type"]),
            params=data.get("params", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class KnowledgeBaseEntry:
    """Entry in the knowledge base for resolving tickets."""
    id: str
    category: str
    keywords: List[str]
    solution: str
    success_rate: float = 0.0
    avg_resolution_time: int = 0


@dataclass
class SystemComponent:
    """Represents a system component that may need checking."""
    name: str
    status: str  # "operational", "degraded", "down"
    last_checked: datetime
    related_categories: List[str]


@dataclass
class EnvironmentState:
    """Full state of the environment."""
    current_ticket: Optional[Ticket] = None
    tickets_in_queue: List[Ticket] = field(default_factory=list)
    action_history: List[AgentAction] = field(default_factory=list)
    knowledge_base: List[KnowledgeBaseEntry] = field(default_factory=list)
    system_components: Dict[str, SystemComponent] = field(default_factory=dict)
    agent_metrics: Dict[str, Any] = field(default_factory=dict)
    episode_step: int = 0
    max_steps: int = 50
    task_difficulty: str = "easy"  # "easy", "medium", "hard"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "current_ticket": self.current_ticket.to_dict() if self.current_ticket else None,
            "tickets_in_queue": [t.to_dict() for t in self.tickets_in_queue],
            "action_history": [a.to_dict() for a in self.action_history],
            "episode_step": self.episode_step,
            "max_steps": self.max_steps,
            "task_difficulty": self.task_difficulty,
            "agent_metrics": self.agent_metrics,
            "system_status": {
                name: {
                    "status": comp.status,
                    "last_checked": comp.last_checked.isoformat(),
                }
                for name, comp in self.system_components.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentState":
        """Create state from dictionary."""
        state = cls(
            current_ticket=Ticket.from_dict(data["current_ticket"]) if data.get("current_ticket") else None,
            episode_step=data.get("episode_step", 0),
            max_steps=data.get("max_steps", 50),
            task_difficulty=data.get("task_difficulty", "easy"),
            agent_metrics=data.get("agent_metrics", {}),
        )
        state.tickets_in_queue = [Ticket.from_dict(t) for t in data.get("tickets_in_queue", [])]
        state.action_history = [AgentAction.from_dict(a) for a in data.get("action_history", [])]
        return state


@dataclass
class StepResult:
    """Result of a step in the environment."""
    state: EnvironmentState
    reward: float
    done: bool
    info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "reward": self.reward,
            "done": self.done,
            "info": self.info,
        }


@dataclass
class Observation:
    """Agent observation at each step."""
    ticket_summary: str
    available_actions: List[ActionType]
    context: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """Convert observation to text format for LLM agents."""
        lines = [
            f"Ticket: {self.ticket_summary}",
            "",
            "Available Actions:",
        ]
        for i, action in enumerate(self.available_actions, 1):
            lines.append(f"  {i}. {action.value}")

        if self.context:
            lines.extend(["", "Context:"])
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_summary": self.ticket_summary,
            "available_actions": [a.value for a in self.available_actions],
            "context": self.context,
        }
