"""
SOC Alert Triage Environment - FastAPI Application
OpenEnv Hackathon Submission - Meta PyTorch 2026
"""
import os
import json
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

from models import (
    TaskDifficulty, TriageAction, TriageActionType,
    AlertSeverity, ResponseAction
)
from server.environment import SOCTriageEnvironment

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
    difficulty: Optional[str] = "easy"
    task_difficulty: Optional[str] = None  # Support both field names


class StepRequest(BaseModel):
    session_id: str
    action: Dict[str, Any]


class GraderRequest(BaseModel):
    session_id: str


# Core OpenEnv Endpoints
@app.post("/reset")
async def reset(request: Request):
    """
    Reset environment for new episode.
    Required OpenEnv endpoint.
    Accepts both JSON body and empty body (defaults to easy).
    """
    try:
        # Try to parse JSON body
        try:
            body = await request.json()
            req_data = ResetRequest(**body)
            # Support both difficulty and task_difficulty
            difficulty_str = req_data.difficulty or req_data.task_difficulty or "easy"
        except Exception:
            # Empty body or invalid JSON - default to easy
            difficulty_str = "easy"

        difficulty = TaskDifficulty(difficulty_str.lower())
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
async def grader(request: Request):
    """
    Return grader score after episode completion.
    Required for hackathon.
    Returns score between 0.0-1.0.
    Accepts both query params and JSON body.
    """
    session_id = None

    # Try to get from query params first
    try:
        session_id = request.query_params.get("session_id")
    except:
        pass

    # If not in query params, try JSON body
    if not session_id:
        try:
            body = await request.json()
            session_id = body.get("session_id")
        except:
            pass

    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id parameter")

    if session_id not in environments:
        raise HTTPException(status_code=404, detail="Session not found")

    env = environments[session_id]

    # Use current score directly
    score = float(env._env_state.current_score)

    return {
        "session_id": session_id,
        "score": round(score, 4),
        "difficulty": env._env_state.task_difficulty.value,
        "steps_taken": env._env_state.step_count,
        "max_steps": env.config.max_steps if env.config else 0,
        "alerts_processed": env._env_state.alerts_classified,
        "total_alerts": env._env_state.total_alerts,
        "incidents_created": env._env_state.incidents_created,
        "campaigns_reported": env._env_state.campaigns_reported,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/baseline")
async def baseline():
    """
    Trigger baseline inference and return scores for all 3 tasks.
    Required for hackathon.
    """
    try:
        # Run the inference script
        result = subprocess.run(
            ["python", "inference.py"],
            capture_output=True,
            text=True,
            timeout=1200,  # 20 minute timeout
            cwd=os.getcwd()
        )

        # Parse the output to find the JSON result
        stdout = result.stdout
        stderr_output = result.stderr

        # Look for FINAL_OUTPUT or JSON in output
        scores = {"easy": 0.0, "medium": 0.0, "hard": 0.0}

        # Try to parse from stdout
        try:
            # Look for the final output marker
            if "FINAL_OUTPUT:" in stdout:
                json_start = stdout.find("FINAL_OUTPUT:") + len("FINAL_OUTPUT:")
                json_str = stdout[json_start:].strip()
                # Find the end of the JSON object
                brace_count = 0
                json_end = 0
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                if json_end > 0:
                    parsed = json.loads(json_str[:json_end])
                    if "scores" in parsed:
                        scores = parsed["scores"]
                    else:
                        scores = parsed
        except Exception as e:
            print(f"Error parsing baseline output: {e}")

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
            "model": os.environ.get("MODEL_NAME", "gpt-4o-mini")
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "error": "Baseline script timed out after 20 minutes",
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
