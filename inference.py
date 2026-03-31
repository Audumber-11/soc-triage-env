"""
SOC Alert Triage Environment - Inference Script
OpenEnv Hackathon Submission - Meta PyTorch 2026

This script runs the baseline agent against all task difficulties.
Required environment variables:
   - API_BASE_URL: Environment URL (default: http://localhost:8000)
   - MODEL_NAME: Model to use (default: gpt-4o-mini)
   - OPENAI_API_KEY: OpenAI API key for LLM calls (required)
   - HF_TOKEN: HuggingFace token (if needed)

Output: JSON with scores for easy, medium, hard tasks
Runtime: < 20 minutes
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List
from openai import OpenAI

# Configuration from environment
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Initialize OpenAI client if API key available
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

def check_health():
    """Check if environment is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False


def classify_alert_with_llm(alert: Dict[str, Any]) -> str:
    """Use LLM to classify a security alert."""
    if not openai_client:
        return "medium"  # Default fallback

    prompt = f"""Classify this security alert as one of: false_positive, low, medium, high

Alert: {alert.get('alert_type', 'unknown')}
Source: {alert.get('source', 'unknown')}
Severity: {alert.get('severity', 'unknown')}
Description: {alert.get('description', 'none')}

Respond with ONLY the classification."""

    try:
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a SOC analyst. Respond with only one word."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )
        result = response.choices[0].message.content.strip().lower()
        if "false" in result:
            return "false_positive"
        elif result in ["false_positive", "low", "medium", "high"]:
            return result
        return "medium"
    except Exception:
        return "medium"

def run_episode(difficulty: str, max_steps: int = 100) -> Dict[str, Any]:
    """Run a single episode and return results."""
    # Reset environment
    reset_resp = requests.post(
        f"{API_BASE_URL}/reset",
        json={"task_difficulty": difficulty},
        timeout=30
    )
    reset_data = reset_resp.json()
    session_id = reset_data.get("session_id")

    if not session_id:
        return {"error": "Failed to reset environment"}

    # Run steps using LLM agent if available
    state = reset_data.get("state", {})
    done = False
    steps = 0

    while not done and steps < max_steps:
        alerts = state.get("alerts", [])
        if not alerts:
            break

        # Use LLM for classification if available, otherwise fallback
        alert = alerts[0]
        classification = classify_alert_with_llm(alert) if openai_client else "medium"
        
        action = {
            "action_type": "classify_alert",
            "alert_id": alert.get("alert_id"),
            "classification": classification
        }

        step_resp = requests.post(
            f"{API_BASE_URL}/step",
            json={"session_id": session_id, "action": action},
            timeout=30
        )
        step_data = step_resp.json()
        state = step_data.get("state", {})
        done = step_data.get("done", False)
        steps += 1

    # Get score
    grader_resp = requests.post(
        f"{API_BASE_URL}/grader",
        json={"session_id": session_id},
        timeout=30
    )
    grader_data = grader_resp.json()

    return {
        "difficulty": difficulty,
        "steps": steps,
        "score": grader_data.get("score", 0.0),
        "metrics": grader_data.get("metrics", {})
    }

def run_baseline():
    """Run baseline on all difficulties and return scores."""
    print("=" * 50)
    print("SOC Alert Triage - Inference Script")
    print("=" * 50)

    # Check health
    print("\n[1/4] Checking environment health...")
    if not check_health():
        print(f"ERROR: Cannot connect to {API_BASE_URL}")
        print("Make sure the environment is running.")
        sys.exit(1)
    print("✓ Environment is healthy")

    # Run tasks
    results = {}
    difficulties = ["easy", "medium", "hard"]

    for i, difficulty in enumerate(difficulties, 2):
        print(f"\n[{i}/4] Running {difficulty} task...")
        start_time = time.time()
        result = run_episode(difficulty)
        elapsed = time.time() - start_time
        results[difficulty] = result
        print(f"✓ Score: {result['score']:.4f} (took {elapsed:.1f}s)")

    # Calculate average
    avg_score = sum(r["score"] for r in results.values()) / 3

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(json.dumps({
        "easy": round(results["easy"]["score"], 4),
        "medium": round(results["medium"]["score"], 4),
        "hard": round(results["hard"]["score"], 4),
        "average": round(avg_score, 4)
    }, indent=2))
    print("=" * 50)

    return {
        "status": "success",
        "scores": {
            "easy": round(results["easy"]["score"], 4),
            "medium": round(results["medium"]["score"], 4),
            "hard": round(results["hard"]["score"], 4),
        },
        "average": round(avg_score, 4)
    }

if __name__ == "__main__":
    try:
        results = run_baseline()
        # Output final JSON for evaluation
        print("\nFINAL_OUTPUT:")
        print(json.dumps(results))
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
