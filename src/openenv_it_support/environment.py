"""Main IT Support Environment implementing OpenEnv spec."""

import random
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

from .models import (
    Ticket, TicketStatus, AgentAction, EnvironmentState, StepResult,
    ActionType, KnowledgeBaseEntry, SystemComponent, Observation
)
from .data import get_tickets_by_difficulty, get_knowledge_base, get_system_components
from .graders import create_grader, BaseGrader


class ITSupportEnvironment:
    """
    OpenEnv-compliant IT Support Ticket Resolution Environment.

    Agents learn to handle real-world IT support tickets through:
    - Gathering information (view ticket, search KB, check systems)
    - Applying fixes (based on knowledge base solutions)
    - Communicating with users (notifications, comments)
    - Managing escalations appropriately
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the IT Support environment.

        Args:
            config_path: Path to openenv.yaml configuration file
        """
        self.config = self._load_config(config_path)
        self.state: Optional[EnvironmentState] = None
        self.grader: Optional[BaseGrader] = None
        self.current_difficulty: str = "easy"
        self.episode_count: int = 0

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from openenv.yaml."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)

        # Default configuration
        return {
            "environment": {
                "name": "it-support-tickets",
                "version": "1.0.0",
                "description": "IT support ticket resolution environment",
                "max_steps_per_episode": 50,
            },
            "observation_space": {
                "type": "text",
                "description": "Text description of current ticket and available actions",
            },
            "action_space": {
                "type": "discrete",
                "actions": [a.value for a in ActionType],
            },
            "tasks": {
                "easy": {
                    "description": "Simple one or two-step ticket resolutions",
                    "episodes": 5,
                },
                "medium": {
                    "description": "Multi-step diagnostic process required",
                    "episodes": 5,
                },
                "hard": {
                    "description": "Complex multi-system issues",
                    "episodes": 5,
                },
            },
        }

    def reset(self, difficulty: Optional[str] = None, ticket_id: Optional[str] = None) -> Observation:
        """
        Reset environment to initial state for a new episode.

        Args:
            difficulty: 'easy', 'medium', or 'hard'. If None, cycles through difficulties.
            ticket_id: Specific ticket to load (for testing). If None, random selection.

        Returns:
            Initial observation
        """
        # Determine difficulty
        if difficulty:
            self.current_difficulty = difficulty
        else:
            difficulties = ["easy", "medium", "hard"]
            self.current_difficulty = difficulties[self.episode_count % 3]

        self.episode_count += 1

        # Create state
        self.state = EnvironmentState(
            max_steps=self.config.get("environment", {}).get("max_steps_per_episode", 50),
            task_difficulty=self.current_difficulty,
        )

        # Load knowledge base and system components
        self.state.knowledge_base = get_knowledge_base()
        self.state.system_components = get_system_components()

        # Load tickets for this difficulty
        tickets = get_tickets_by_difficulty(self.current_difficulty)

        if ticket_id:
            tickets = [t for t in tickets if t.id == ticket_id]
            if not tickets:
                raise ValueError(f"Ticket {ticket_id} not found")
            self.state.current_ticket = tickets[0]
        else:
            self.state.current_ticket = random.choice(tickets)

        # Store remaining tickets in queue
        self.state.tickets_in_queue = [t for t in tickets if t.id != self.state.current_ticket.id]

        # Initialize grader
        self.grader = create_grader(self.state.current_ticket, self.current_difficulty)

        # Reset step counter
        self.state.episode_step = 0
        self.state.agent_metrics = {
            "start_time": datetime.now().isoformat(),
            "difficulty": self.current_difficulty,
        }

        return self._get_observation()

    def step(self, action: Union[AgentAction, Dict[str, Any], str]) -> StepResult:
        """
        Execute one step in the environment.

        Args:
            action: AgentAction, dict with 'action_type' and 'params', or action type string

        Returns:
            StepResult with new state, reward, done flag, and info
        """
        if self.state is None:
            raise RuntimeError("Environment not reset. Call reset() first.")

        # Parse action
        if isinstance(action, dict):
            action = AgentAction(
                action_type=ActionType(action["action_type"]),
                params=action.get("params", {}),
            )
        elif isinstance(action, str):
            action = AgentAction(
                action_type=ActionType(action),
                params={},
            )
        elif not isinstance(action, AgentAction):
            raise ValueError(f"Invalid action type: {type(action)}")

        # Execute action
        self._execute_action(action)

        # Update state
        self.state.episode_step += 1
        self.state.action_history.append(action)

        # Calculate reward
        reward = self.grader.grade(self.state, action)

        # Check if done
        done = self.grader.is_done(self.state)

        # Update ticket time
        if self.state.current_ticket:
            self.state.current_ticket.time_spent_minutes += 5  # Each step = 5 minutes

        # Prepare info
        info = {
            "step": self.state.episode_step,
            "max_steps": self.state.max_steps,
            "difficulty": self.current_difficulty,
            "ticket_id": self.state.current_ticket.id if self.state.current_ticket else None,
            "ticket_status": self.state.current_ticket.status.value if self.state.current_ticket else None,
            "fixes_applied": list(self.grader.resolved_fixes) if self.grader else [],
            "fixes_required": list(self.state.current_ticket.required_fixes) if self.state.current_ticket else [],
        }

        if done:
            info["final_score"] = reward
            info["completion"] = "success" if self.state.current_ticket and self.state.current_ticket.status == TicketStatus.RESOLVED else "timeout"

        return StepResult(
            state=self.state,
            reward=reward,
            done=done,
            info=info,
        )

    def _execute_action(self, action: AgentAction) -> None:
        """Execute the action and update internal state."""
        ticket = self.state.current_ticket

        if action.action_type == ActionType.ASSIGN_TICKET:
            if ticket:
                ticket.assigned_to = "AI_Agent"
                ticket.status = TicketStatus.IN_PROGRESS

        elif action.action_type == ActionType.ADD_COMMENT:
            if ticket:
                comment = {
                    "author": "AI_Agent",
                    "text": action.params.get("comment", ""),
                    "timestamp": datetime.now().isoformat(),
                }
                ticket.comments.append(comment)

        elif action.action_type == ActionType.APPLY_FIX:
            if ticket:
                fix_type = action.params.get("fix_type", "")
                success = self._simulate_fix_application(fix_type)

                if success and fix_type in ticket.required_fixes:
                    ticket.applied_fixes.add(fix_type)

                # Add result as comment
                ticket.comments.append({
                    "author": "AI_Agent",
                    "text": f"Applied fix: {fix_type} - {'Success' if success else 'Failed'}",
                    "timestamp": datetime.now().isoformat(),
                })

                ticket.resolution_attempts += 1

        elif action.action_type == ActionType.ESCALATE:
            if ticket:
                ticket.escalation_level += 1
                ticket.status = TicketStatus.PENDING
                ticket.comments.append({
                    "author": "AI_Agent",
                    "text": f"Escalated to level {ticket.escalation_level}",
                    "timestamp": datetime.now().isoformat(),
                })

        elif action.action_type == ActionType.NOTIFY_USER:
            if ticket:
                ticket.comments.append({
                    "author": "AI_Agent",
                    "text": action.params.get("message", "Update provided to user"),
                    "timestamp": datetime.now().isoformat(),
                })

        elif action.action_type == ActionType.REQUEST_INFO:
            if ticket:
                # Simulate getting additional information
                additional_info = self._simulate_info_request(action.params.get("query", ""))
                ticket.comments.append({
                    "author": "System",
                    "text": f"Additional info: {additional_info}",
                    "timestamp": datetime.now().isoformat(),
                })

        elif action.action_type == ActionType.RESOLVE:
            if ticket:
                # Check if resolution is valid
                if ticket.applied_fixes >= ticket.required_fixes:
                    ticket.status = TicketStatus.RESOLVED
                    ticket.comments.append({
                        "author": "AI_Agent",
                        "text": "Ticket resolved successfully",
                        "timestamp": datetime.now().isoformat(),
                    })
                else:
                    ticket.comments.append({
                        "author": "AI_Agent",
                        "text": "Attempted resolution - fixes incomplete",
                        "timestamp": datetime.now().isoformat(),
                    })

        elif action.action_type == ActionType.CLOSE:
            if ticket:
                if ticket.status == TicketStatus.RESOLVED:
                    ticket.status = TicketStatus.CLOSED
                else:
                    # Cannot close unresolved ticket
                    pass

        # VIEW_TICKET, SEARCH_KNOWLEDGE_BASE, CHECK_SYSTEM_STATUS are passive (info gathering)

    def _simulate_fix_application(self, fix_type: str) -> bool:
        """Simulate applying a fix with realistic success probability."""
        # Base success rate varies by fix complexity
        base_success = 0.85

        # Adjust based on difficulty
        if self.current_difficulty == "hard":
            base_success = 0.70
        elif self.current_difficulty == "medium":
            base_success = 0.80

        # Some fixes are inherently harder
        hard_fixes = ["check_ad_health", "check_dfs_health", "check_cache_status"]
        if fix_type in hard_fixes:
            base_success -= 0.15

        return random.random() < base_success

    def _simulate_info_request(self, query: str) -> str:
        """Simulate getting additional information from user."""
        responses = [
            "Issue started after the latest update.",
            "Only affecting this specific machine.",
            "Tried restarting already, didn't help.",
            "Error appears intermittently, roughly every hour.",
            "Other users in the same department are not affected.",
            "Started happening this morning, was working fine yesterday.",
        ]
        return random.choice(responses)

    def _get_observation(self) -> Observation:
        """Generate current observation for the agent."""
        ticket = self.state.current_ticket

        if not ticket:
            return Observation(
                ticket_summary="No active ticket",
                available_actions=[],
            )

        # Build ticket summary
        summary_lines = [
            f"ID: {ticket.id}",
            f"Title: {ticket.title}",
            f"Priority: {ticket.priority.value.upper()}",
            f"Category: {ticket.category}",
            f"Status: {ticket.status.value}",
            f"Requester: {ticket.requester}",
            f"\nDescription:\n{ticket.description}",
        ]

        if ticket.comments:
            summary_lines.append("\n--- Previous Comments/Notes ---")
            for comment in ticket.comments[-3:]:  # Show last 3 comments
                summary_lines.append(f"[{comment['author']}] {comment['text']}")

        # Determine available actions based on state
        available_actions = list(ActionType)

        # Some actions may be restricted based on ticket status
        if ticket.status == TicketStatus.RESOLVED:
            available_actions = [a for a in available_actions if a in [ActionType.CLOSE, ActionType.ADD_COMMENT]]

        context = {
            "step": f"{self.state.episode_step}/{self.state.max_steps}",
            "difficulty": self.current_difficulty,
            "resolution_progress": f"{len(ticket.applied_fixes)}/{len(ticket.required_fixes)} fixes applied",
        }

        # Add KB hint if available
        kb_hints = self._get_kb_hints(ticket)
        if kb_hints:
            context["kb_hints"] = kb_hints

        return Observation(
            ticket_summary="\n".join(summary_lines),
            available_actions=available_actions,
            context=context,
        )

    def _get_kb_hints(self, ticket: Ticket) -> List[str]:
        """Get relevant knowledge base entries for the ticket."""
        hints = []
        for entry in self.state.knowledge_base:
            if entry.category == ticket.category:
                # Simple keyword matching
                keywords_match = any(kw in ticket.description.lower() or kw in ticket.title.lower()
                                   for kw in entry.keywords)
                if keywords_match:
                    hints.append(f"[{entry.id}] {entry.solution[:100]}...")
        return hints[:2]  # Return top 2 hints

    def state(self) -> EnvironmentState:
        """
        Get current environment state.

        Returns:
            Current EnvironmentState
        """
        if self.state is None:
            raise RuntimeError("Environment not reset. Call reset() first.")
        return self.state

    def render(self) -> str:
        """
        Render current state as human-readable text.

        Returns:
            Text representation of current state
        """
        if self.state is None:
            return "Environment not initialized. Call reset() first."

        obs = self._get_observation()
        return obs.to_text()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for the current/last episode.

        Returns:
            Dictionary of metrics
        """
        if self.state is None:
            return {}

        ticket = self.state.current_ticket
        return {
            "episode": self.episode_count,
            "difficulty": self.current_difficulty,
            "steps_taken": self.state.episode_step,
            "max_steps": self.state.max_steps,
            "ticket_id": ticket.id if ticket else None,
            "ticket_resolved": ticket.status == TicketStatus.RESOLVED if ticket else False,
            "resolution_attempts": ticket.resolution_attempts if ticket else 0,
            "time_spent_minutes": ticket.time_spent_minutes if ticket else 0,
            "action_count": len(self.state.action_history),
        }

    def export_episode(self, path: str) -> None:
        """Export episode data to file."""
        if self.state is None:
            raise RuntimeError("No episode to export")

        data = {
            "metrics": self.get_metrics(),
            "ticket": self.state.current_ticket.to_dict() if self.state.current_ticket else None,
            "actions": [a.to_dict() for a in self.state.action_history],
            "config": self.config,
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


class BatchEvaluator:
    """Evaluate agent performance across multiple episodes."""

    def __init__(self, env: ITSupportEnvironment):
        self.env = env
        self.results: List[Dict[str, Any]] = []

    def run_episodes(self, agent_fn, num_episodes: int = 15, difficulties: List[str] = None) -> Dict[str, Any]:
        """
        Run multiple episodes and compute aggregate metrics.

        Args:
            agent_fn: Function that takes observation and returns action
            num_episodes: Number of episodes to run
            difficulties: List of difficulties to test (cycles through if None)

        Returns:
            Aggregate metrics
        """
        if difficulties is None:
            difficulties = ["easy", "medium", "hard"]

        self.results = []

        for i in range(num_episodes):
            difficulty = difficulties[i % len(difficulties)]

            obs = self.env.reset(difficulty=difficulty)
            episode_reward = 0.0
            steps = 0

            while True:
                action = agent_fn(obs)
                result = self.env.step(action)

                episode_reward += result.reward
                steps += 1
                obs = self.env._get_observation()

                if result.done:
                    break

            metrics = self.env.get_metrics()
            metrics["total_reward"] = episode_reward
            metrics["final_score"] = result.reward if result.done else 0  # Final step reward

            self.results.append(metrics)

        return self._compute_aggregate_metrics()

    def _compute_aggregate_metrics(self) -> Dict[str, Any]:
        """Compute aggregate statistics across all episodes."""
        if not self.results:
            return {}

        by_difficulty = {"easy": [], "medium": [], "hard": []}

        for r in self.results:
            diff = r.get("difficulty", "easy")
            if diff in by_difficulty:
                by_difficulty[diff].append(r)

        def avg(scores):
            return sum(scores) / len(scores) if scores else 0.0

        aggregate = {
            "overall": {
                "episodes": len(self.results),
                "avg_final_score": avg([r.get("final_score", 0) for r in self.results]),
                "avg_steps": avg([r.get("steps_taken", 0) for r in self.results]),
                "resolution_rate": sum(1 for r in self.results if r.get("ticket_resolved")) / len(self.results),
            },
            "by_difficulty": {},
        }

        for diff, results in by_difficulty.items():
            if results:
                aggregate["by_difficulty"][diff] = {
                    "episodes": len(results),
                    "avg_final_score": avg([r.get("final_score", 0) for r in results]),
                    "avg_steps": avg([r.get("steps_taken", 0) for r in results]),
                    "resolution_rate": sum(1 for r in results if r.get("ticket_resolved")) / len(results),
                }

        return aggregate

    def export_results(self, path: str) -> None:
        """Export results to JSON file."""
        data = {
            "episodes": self.results,
            "aggregate": self._compute_aggregate_metrics(),
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
