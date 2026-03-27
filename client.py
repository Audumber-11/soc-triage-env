"""
SOC Alert Triage Environment - Client
OpenEnv Hackathon Submission - Meta PyTorch 2026
"""
import requests
from typing import Optional, Dict, Any
from models import TriageAction, TriageObservation, TriageState, TaskDifficulty


class SOCTriageClient:
    """
    Client for SOC Alert Triage Environment.
    Synchronous client for interacting with the environment.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session_id: Optional[str] = None

    def reset(self, difficulty: TaskDifficulty = TaskDifficulty.EASY) -> TriageObservation:
        """Reset environment and start new episode."""
        response = requests.post(
            f"{self.base_url}/reset",
            json={"task_difficulty": difficulty.value}
        )
        response.raise_for_status()
        data = response.json()

        self.session_id = data["session_id"]
        return TriageObservation(**data["observation"])

    def step(self, action: TriageAction) -> TriageObservation:
        """Execute action in environment."""
        if not self.session_id:
            raise ValueError("Environment not reset. Call reset() first.")

        response = requests.post(
            f"{self.base_url}/step",
            json={
                "session_id": self.session_id,
                "action": action.dict(exclude_none=True)
            }
        )
        response.raise_for_status()
        data = response.json()

        return TriageObservation(**data["observation"])

    def get_state(self) -> Dict[str, Any]:
        """Get current environment state."""
        if not self.session_id:
            raise ValueError("Environment not reset. Call reset() first.")

        response = requests.get(f"{self.base_url}/state/{self.session_id}")
        response.raise_for_status()
        return response.json()

    def get_tasks(self) -> Dict[str, Any]:
        """Get task definitions."""
        response = requests.get(f"{self.base_url}/tasks")
        response.raise_for_status()
        return response.json()

    def get_grader_score(self) -> Dict[str, Any]:
        """Get grader score for current episode."""
        if not self.session_id:
            raise ValueError("Environment not reset. Call reset() first.")

        response = requests.post(
            f"{self.base_url}/grader",
            params={"session_id": self.session_id}
        )
        response.raise_for_status()
        return response.json()

    def run_baseline(self) -> Dict[str, Any]:
        """Run baseline script and get scores."""
        response = requests.post(f"{self.base_url}/baseline")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check environment health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()


class SyncSOCTriageEnv:
    """Synchronous wrapper for SOC Triage Environment."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = SOCTriageClient(base_url)

    def __enter__(self):
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def reset(self, difficulty: str = "easy"):
        """Reset with string difficulty."""
        return self.client.reset(TaskDifficulty(difficulty))

    def step(self, action: Dict[str, Any]):
        """Step with dict action."""
        triage_action = TriageAction(**action)
        return self.client.step(triage_action)
