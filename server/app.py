"""
SOC Alert Triage Environment - FastAPI Application
OpenEnv Hackathon Submission - Meta PyTorch 2026
"""
import os
import json
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import (
    TaskDifficulty, TriageAction, TriageActionType,
    AlertSeverity, ResponseAction
)
from environment import SOCTriageEnvironment

app = FastAPI(
    title="SOC Alert Triage Environment",
    description="OpenEnv environment for Security Operations Center alert triage",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store environments per session
environments: Dict[str, SOCTriageEnvironment] = {}


# Request/Response Models
class ResetRequest(BaseModel):
    task_difficulty: str = "easy"


class StepRequest(BaseModel):
    session_id: str
    action: Dict[str, Any]


class TaskResponse(BaseModel):
    name: str
    difficulty: str
    description: str
    max_steps: int
    num_alerts: int
    scoring_criteria: str


class ActionSchema(BaseModel):
    action_type: str
    description: str
    parameters: Dict[str, str]


# Core OpenEnv Endpoints
@app.post("/reset")
async def reset(request: ResetRequest):
    """
    Reset environment for new episode.
    Required OpenEnv endpoint.
    """
    try:
        difficulty = TaskDifficulty(request.task_difficulty.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid difficulty. Use: easy, medium, hard")

    # Create new environment
    env = SOCTriageEnvironment()
    observation = env.reset(difficulty)

    # Store environment
    environments[env._env_state.episode_id] = env

    return {
        "session_id": env._env_state.episode_id,
        "observation": observation.dict(),
        "state": env._env_state.dict(),
        "config": env.config.dict()
    }


@app.post("/step")
async def step(request: StepRequest):
    """
    Execute action in environment.
    Required OpenEnv endpoint.
    """
    if request.session_id not in environments:
        raise HTTPException(status_code=404, detail="Session not found")

    env = environments[request.session_id]

    # Parse action
    try:
        action_data = request.action
        action = TriageAction(
            action_type=TriageActionType(action_data.get("action_type", "classify_alert")),
            alert_id=action_data.get("alert_id"),
            incident_id=action_data.get("incident_id"),
            classification=AlertSeverity(action_data.get("classification")) if action_data.get("classification") else None,
            root_cause=action_data.get("root_cause"),
            investigation_query=action_data.get("investigation_query"),
            response_action=ResponseAction(action_data.get("response_action")) if action_data.get("response_action") else None,
            campaign_id=action_data.get("campaign_id"),
            confidence=action_data.get("confidence", 0.5)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid action: {str(e)}")

    # Execute step
    observation = env.step(action)

    return {
        "session_id": request.session_id,
        "observation": observation.dict(),
        "state": env._env_state.dict()
    }


@app.get("/state/{session_id}")
async def get_state(session_id: str):
    """
    Get current environment state.
    Required OpenEnv endpoint.
    """
    if session_id not in environments:
        raise HTTPException(status_code=404, detail="Session not found")

    env = environments[session_id]

    return {
        "session_id": session_id,
        "state": env._env_state.dict(),
        "config": env.config.dict() if env.config else None
    }


# Hackathon Required Endpoints
@app.get("/tasks")
async def get_tasks():
    """
    Return list of tasks and action schema.
    Required for hackathon.
    """
    tasks = [
        {
            "name": "Basic Alert Classification",
            "difficulty": "easy",
            "description": "Classify individual security alerts as false_positive, low, medium, or high priority. "
                        "The agent receives alerts one at a time and must correctly label each based on alert content.",
            "max_steps": 25,
            "num_alerts": 20,
            "false_positive_rate": 0.4,
            "scoring_criteria": "Classification accuracy (0.0-1.0). Penalties for over-escalation.",
            "target_score": 0.85
        },
        {
            "name": "Multi-Source Incident Correlation",
            "difficulty": "medium",
            "description": "Correlate related alerts from different security sources (firewall, IDS, endpoint, cloud) "
                        "into security incidents. Identify root causes and affected assets.",
            "max_steps": 60,
            "num_alerts": 50,
            "false_positive_rate": 0.5,
            "noise_level": 0.3,
            "scoring_criteria": "F1 score (precision + recall) of incident correlation (0.0-1.0)",
            "target_score": 0.75
        },
        {
            "name": "APT Campaign Detection",
            "difficulty": "hard",
            "description": "Detect Advanced Persistent Threat campaigns over 30 days of noisy alert data. "
                        "Correlate incidents, identify attack progression, and recommend responses. "
                        "70% of alerts are false positives. Requires strategic investigation decisions.",
            "max_steps": 150,
            "num_alerts": 200,
            "false_positive_rate": 0.7,
            "noise_level": 0.5,
            "time_span_days": 30,
            "scoring_criteria": "Weighted: Campaign detection (25%), Correlation (25%), Classification (20%), "
                              "Investigation efficiency (15%), Response appropriateness (15%)",
            "target_score": 0.65
        }
    ]

    action_schema = {
        "classify_alert": {
            "description": "Classify a single alert",
            "required_params": ["alert_id", "classification"],
            "classification_options": ["false_positive", "low", "medium", "high"]
        },
        "create_incident": {
            "description": "Create a new incident for correlated alerts",
            "required_params": ["incident_id"]
        },
        "add_to_incident": {
            "description": "Add an alert to an existing incident",
            "required_params": ["alert_id", "incident_id"]
        },
        "set_root_cause": {
            "description": "Identify root cause of an incident",
            "required_params": ["incident_id", "root_cause"]
        },
        "investigate": {
            "description": "Deep investigation of an alert",
            "required_params": ["alert_id"],
            "optional_params": ["investigation_query"]
        },
        "escalate": {
            "description": "Escalate incident to senior analyst",
            "required_params": ["incident_id"]
        },
        "report_campaign": {
            "description": "Report detected APT campaign",
            "required_params": ["campaign_id", "incident_ids"]
        },
        "set_response": {
            "description": "Set response action",
            "required_params": ["incident_id", "response_action"],
            "response_options": ["monitor", "contain", "isolate", "block", "eradicate", "recover"]
        }
    }

    return {
        "tasks": tasks,
        "action_schema": action_schema,
        "environment": "SOC Alert Triage",
        "description": "Security Operations Center alert triage, incident correlation, and threat detection"
    }


@app.post("/grader")
async def grader(session_id: str):
    """
    Return grader score after episode completion.
    Required for hackathon.
    Returns score between 0.0-1.0.
    """
    if session_id not in environments:
        raise HTTPException(status_code=404, detail="Session not found")

    env = environments[session_id]
    score = env._env_state.current_score

    # Ensure score is in 0.0-1.0 range
    score = max(0.0, min(1.0, score))

    # Calculate additional metrics
    metrics = {
        "classification_accuracy": env._calculate_easy_score() if hasattr(env, '_calculate_easy_score') else 0,
        "correlation_f1": env._calculate_medium_score() if hasattr(env, '_calculate_medium_score') else 0,
        "campaign_detection": env._check_campaign_accuracy(list(env.agent_campaigns.values())[0]) if env.agent_campaigns else 0
    }

    return {
        "session_id": session_id,
        "score": round(score, 4),
        "difficulty": env.state.task_difficulty.value,
        "steps_taken": env.state.step_count,
        "max_steps": env.config.max_steps if env.config else 0,
        "alerts_processed": env.state.alerts_classified,
        "total_alerts": env.state.total_alerts,
        "incidents_created": env.state.incidents_created,
        "campaigns_reported": env.state.campaigns_reported,
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/baseline")
async def baseline():
    """
    Trigger baseline inference and return scores for all 3 tasks.
    Required for hackathon.
    """
    try:
        # Run baseline script
        result = subprocess.run(
            ["python", "baseline.py"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd="/app"  # Docker working directory
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "error": result.stderr,
                "scores": {"easy": 0.0, "medium": 0.0, "hard": 0.0}
            }

        # Parse results
        try:
            scores = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Try to extract JSON from output
            output = result.stdout.strip()
            if "{" in output:
                json_start = output.find("{")
                scores = json.loads(output[json_start:])
            else:
                scores = {"easy": 0.0, "medium": 0.0, "hard": 0.0}

        # Validate scores
        validated_scores = {
            "easy": max(0.0, min(1.0, float(scores.get("easy", 0.0)))),
            "medium": max(0.0, min(1.0, float(scores.get("medium", 0.0)))),
            "hard": max(0.0, min(1.0, float(scores.get("hard", 0.0))))
        }

        return {
            "status": "success",
            "scores": validated_scores,
            "average": round(sum(validated_scores.values()) / 3, 4),
            "timestamp": datetime.utcnow().isoformat(),
            "model": "gpt-4o-mini"  # Baseline model used
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": "Baseline script timed out after 10 minutes",
            "scores": {"easy": 0.0, "medium": 0.0, "hard": 0.0}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "scores": {"easy": 0.0, "medium": 0.0, "hard": 0.0}
        }


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Required for deployment validation.
    """
    return {
        "status": "ok",
        "environment": "soc-triage-env",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SOC Alert Triage Environment",
        "description": "OpenEnv environment for security operations center alert triage",
        "endpoints": [
            "/reset",
            "/step",
            "/state/{session_id}",
            "/tasks",
            "/grader",
            "/baseline",
            "/health"
        ],
        "version": "1.0.0"
    }


# Cleanup endpoint for memory management
@app.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up environment session."""
    if session_id in environments:
        del environments[session_id]
        return {"status": "cleaned"}
    return {"status": "not_found"}
