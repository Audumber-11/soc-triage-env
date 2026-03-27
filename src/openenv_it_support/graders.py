"""Grader implementations for different task difficulties."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Set
from .models import Ticket, TicketStatus, AgentAction, ActionType, EnvironmentState


class BaseGrader(ABC):
    """Base class for ticket graders."""

    def __init__(self, ticket: Ticket):
        self.ticket = ticket
        self.resolved_fixes: Set[str] = set()
        self.action_sequence: List[AgentAction] = []
        self.optimal_steps: int = 5
        self.penalty_escalation: bool = False

    def grade(self, state: EnvironmentState, action: AgentAction) -> float:
        """Grade the current step and return reward."""
        self.action_sequence.append(action)

        # Check if ticket is resolved
        if state.current_ticket and state.current_ticket.status == TicketStatus.RESOLVED:
            return self._calculate_final_score()

        # Check if episode is done without resolution
        if state.episode_step >= state.max_steps:
            return self._calculate_partial_score(state)

        # Intermediate step reward
        return self._calculate_step_reward(action)

    def _calculate_final_score(self) -> float:
        """Calculate final score when ticket is resolved."""
        base_score = 1.0

        # Efficiency penalty for too many steps
        steps_taken = len(self.action_sequence)
        if steps_taken > self.optimal_steps:
            efficiency_penalty = min(0.3, (steps_taken - self.optimal_steps) * 0.05)
            base_score -= efficiency_penalty

        # Penalty for unnecessary escalation
        if self.penalty_escalation:
            escalation_count = sum(1 for a in self.action_sequence if a.action_type == ActionType.ESCALATE)
            base_score -= min(0.2, escalation_count * 0.1)

        return max(0.0, min(1.0, base_score))

    def _calculate_partial_score(self, state: EnvironmentState) -> float:
        """Calculate partial score when episode ends without resolution."""
        # Calculate completion based on fixes applied
        if self.ticket.required_fixes:
            completion_ratio = len(self.resolved_fixes) / len(self.ticket.required_fixes)
            return completion_ratio * 0.5  # Max 0.5 for partial completion
        return 0.0

    @abstractmethod
    def _calculate_step_reward(self, action: AgentAction) -> float:
        """Calculate reward for a single step."""
        pass

    def is_done(self, state: EnvironmentState) -> bool:
        """Check if episode should end."""
        if state.current_ticket and state.current_ticket.status == TicketStatus.RESOLVED:
            return True
        if state.episode_step >= state.max_steps:
            return True
        return False


class EasyTicketGrader(BaseGrader):
    """Grader for easy tickets - simple one or two-step resolutions."""

    def __init__(self, ticket: Ticket):
        super().__init__(ticket)
        self.optimal_steps = 4
        self.identified_solution = False

    def _calculate_step_reward(self, action: AgentAction) -> float:
        """Reward appropriate actions for easy tickets."""
        reward = 0.0

        # Reward for identifying the ticket
        if action.action_type == ActionType.VIEW_TICKET and not self.identified_solution:
            reward = 0.05
            self.identified_solution = True

        # Reward for searching KB when needed
        elif action.action_type == ActionType.SEARCH_KNOWLEDGE_BASE:
            if self.ticket.category in ["access", "hardware"]:
                reward = 0.1
            else:
                reward = 0.02  # Small reward for KB search in any case

        # Reward for applying correct fix
        elif action.action_type == ActionType.APPLY_FIX:
            fix_type = action.params.get("fix_type", "")
            if fix_type in self.ticket.required_fixes:
                reward = 0.3
                self.resolved_fixes.add(fix_type)
            else:
                reward = -0.05  # Penalty for wrong fix

        # Reward for notifying user
        elif action.action_type == ActionType.NOTIFY_USER:
            if len(self.resolved_fixes) >= len(self.ticket.required_fixes) * 0.5:
                reward = 0.1

        # Reward for resolving
        elif action.action_type == ActionType.RESOLVE:
            if len(self.resolved_fixes) >= len(self.ticket.required_fixes):
                reward = 0.5
            else:
                reward = -0.1  # Penalty for premature resolution

        # Small penalty for unnecessary escalation
        elif action.action_type == ActionType.ESCALATE:
            reward = -0.05

        return reward


class MediumTicketGrader(BaseGrader):
    """Grader for medium tickets - multi-step diagnostic process required."""

    def __init__(self, ticket: Ticket):
        super().__init__(ticket)
        self.optimal_steps = 8
        self.penalty_escalation = True
        self.diagnostics_done: Set[str] = set()
        self.informed_user = False

    def _calculate_step_reward(self, action: AgentAction) -> float:
        """Reward diagnostic and resolution workflow for medium tickets."""
        reward = 0.0

        # Reward systematic approach
        if action.action_type == ActionType.VIEW_TICKET:
            reward = 0.02

        # Important: Check system status for network/software issues
        elif action.action_type == ActionType.CHECK_SYSTEM_STATUS:
            if self.ticket.category in ["network", "software"]:
                reward = 0.08
            self.diagnostics_done.add("system_check")

        # Knowledge base search for appropriate categories
        elif action.action_type == ActionType.SEARCH_KNOWLEDGE_BASE:
            reward = 0.05
            self.diagnostics_done.add("kb_search")

        # Diagnostic actions before fix
        elif action.action_type == ActionType.REQUEST_INFO:
            reward = 0.06
            self.diagnostics_done.add("info_request")

        # Assign to self before fixing
        elif action.action_type == ActionType.ASSIGN_TICKET:
            reward = 0.03

        # Apply fix with proper prerequisites
        elif action.action_type == ActionType.APPLY_FIX:
            fix_type = action.params.get("fix_type", "")
            if len(self.diagnostics_done) >= 2:  # Should have done some diagnostics
                if fix_type in self.ticket.required_fixes:
                    reward = 0.25
                    self.resolved_fixes.add(fix_type)
                else:
                    reward = -0.03
            else:
                reward = 0.05  # Small reward but encourage diagnostics first
                if fix_type in self.ticket.required_fixes:
                    self.resolved_fixes.add(fix_type)

        # Communication with user
        elif action.action_type == ActionType.NOTIFY_USER:
            self.informed_user = True
            reward = 0.05

        elif action.action_type == ActionType.ADD_COMMENT:
            reward = 0.03

        # Resolve when ready
        elif action.action_type == ActionType.RESOLVE:
            required = len(self.ticket.required_fixes)
            if len(self.resolved_fixes) >= required and self.informed_user:
                reward = 0.4
            elif len(self.resolved_fixes) >= required * 0.75:
                reward = 0.1  # Partial reward for mostly done
            else:
                reward = -0.15

        # Escalate only when necessary
        elif action.action_type == ActionType.ESCALATE:
            if self.ticket.priority.value in ["critical", "high"] and len(self.resolved_fixes) == 0:
                reward = 0.05  # Appropriate escalation
            else:
                reward = -0.1

        return reward


class HardTicketGrader(BaseGrader):
    """Grader for hard tickets - complex multi-system issues."""

    def __init__(self, ticket: Ticket):
        super().__init__(ticket)
        self.optimal_steps = 15
        self.penalty_escalation = True
        self.diagnostics_sequence: List[str] = []
        self.communication_steps = 0
        self.escalation_justified = False
        self.root_cause_identified = False

    def _calculate_step_reward(self, action: AgentAction) -> float:
        """Reward complex diagnostic and resolution process."""
        reward = 0.0

        # Understanding the problem
        if action.action_type == ActionType.VIEW_TICKET:
            reward = 0.01

        # Critical: Multiple system checks for hard issues
        elif action.action_type == ActionType.CHECK_SYSTEM_STATUS:
            component = action.params.get("component", "")
            if component:
                if component not in self.diagnostics_sequence:
                    reward = 0.06
                    self.diagnostics_sequence.append(component)
                else:
                    reward = -0.02  # Penalty for redundant checks
            else:
                reward = 0.03

        # Deep KB search for complex issues
        elif action.action_type == ActionType.SEARCH_KNOWLEDGE_BASE:
            reward = 0.04
            self.diagnostics_sequence.append("kb_search")

        # Thorough information gathering
        elif action.action_type == ActionType.REQUEST_INFO:
            reward = 0.04
            self.diagnostics_sequence.append("info_request")

        # Documentation is important for hard tickets
        elif action.action_type == ActionType.ADD_COMMENT:
            reward = 0.03
            if "root cause" in action.params.get("comment", "").lower():
                self.root_cause_identified = True
                reward = 0.08

        # Assignment before work
        elif action.action_type == ActionType.ASSIGN_TICKET:
            reward = 0.02

        # Apply fixes with proper diagnosis
        elif action.action_type == ActionType.APPLY_FIX:
            fix_type = action.params.get("fix_type", "")
            diagnostics_done = len(self.diagnostics_sequence)

            if diagnostics_done >= 3 or self.root_cause_identified:  # Require thorough diagnosis
                if fix_type in self.ticket.required_fixes:
                    if fix_type not in self.resolved_fixes:
                        reward = 0.2
                        self.resolved_fixes.add(fix_type)
                    else:
                        reward = -0.02  # Duplicate fix
                else:
                    reward = -0.05  # Wrong fix
            else:
                reward = 0.02  # Encourage diagnostics first
                if fix_type in self.ticket.required_fixes:
                    self.resolved_fixes.add(fix_type)

        # Communication is important
        elif action.action_type == ActionType.NOTIFY_USER:
            self.communication_steps += 1
            if len(self.resolved_fixes) > 0:
                reward = 0.06
            else:
                reward = 0.02  # Status update

        # Resolve when complete
        elif action.action_type == ActionType.RESOLVE:
            required = len(self.ticket.required_fixes)
            fixes_done = len(self.resolved_fixes)

            if fixes_done >= required and self.root_cause_identified:
                reward = 0.35
            elif fixes_done >= required * 0.8:
                reward = 0.15
            else:
                reward = -0.2  # Heavier penalty for premature resolution

        # Escalation for critical complex issues
        elif action.action_type == ActionType.ESCALATE:
            if self.ticket.priority.value == "critical":
                if len(self.diagnostics_sequence) >= 4:
                    self.escalation_justified = True
                    reward = 0.1  # Appropriate escalation
                else:
                    reward = -0.05  # Escalate too early
            else:
                reward = -0.15  # Unnecessary escalation

        return reward

    def _calculate_final_score(self) -> float:
        """Enhanced scoring for hard tickets."""
        base_score = super()._calculate_final_score()

        # Bonus for thorough diagnostics
        if len(self.diagnostics_sequence) >= 4:
            base_score += 0.05

        # Bonus for root cause documentation
        if self.root_cause_identified:
            base_score += 0.05

        # Bonus for proper communication
        if self.communication_steps >= 2:
            base_score += 0.03

        return min(1.0, base_score)


def create_grader(ticket: Ticket, difficulty: str) -> BaseGrader:
    """Factory function to create appropriate grader."""
    if difficulty == "easy":
        return EasyTicketGrader(ticket)
    elif difficulty == "medium":
        return MediumTicketGrader(ticket)
    elif difficulty == "hard":
        return HardTicketGrader(ticket)
    else:
        return EasyTicketGrader(ticket)
