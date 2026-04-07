"""
SOC Alert Triage Environment - Inference Script
OpenEnv Hackathon Submission - Meta PyTorch 2026

Required environment variables:
   - API_BASE_URL: Environment URL (default: http://localhost:8000)
   - MODEL_NAME: Model to use (default: gpt-4o-mini)
   - HF_TOKEN: HuggingFace token (if needed)
   - OPENAI_API_KEY: OpenAI API key for LLM calls (required)

Output: Structured stdout logs with [START], [STEP], and [END] markers
Runtime: < 20 minutes
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, List, Optional
from openai import OpenAI

# Configuration from environment
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

def log_start():
    """Log start marker."""
    print("[START]")
    print(json.dumps({
        "environment": "soc-triage-env",
        "model": MODEL_NAME,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }))

def log_step(step_num: int, action: str, observation_summary: str):
    """Log step marker."""
    print(f"[STEP {step_num}]")
    print(json.dumps({
        "step": step_num,
        "action": action,
        "observation": observation_summary
    }))

def log_end(scores: Dict[str, float]):
    """Log end marker with final scores."""
    print("[END]")
    print(json.dumps({
        "scores": scores,
        "average": round(sum(scores.values()) / 3, 4) if scores else 0.0
    }))

def check_health() -> bool:
    """Check if environment is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def classify_with_llm(alert: Dict[str, Any]) -> str:
    """Use LLM to classify a security alert."""
    if not client:
        return "medium"

    prompt = f"""Classify this security alert as one of: false_positive, low, medium, high

Alert Type: {alert.get('alert_type', 'unknown')}
Source: {alert.get('source', 'unknown')}
Severity: {alert.get('severity', 'unknown')}
Description: {alert.get('description', 'none')}
Source IP: {alert.get('source_ip', 'unknown')}
Destination IP: {alert.get('dest_ip', 'unknown')}
User: {alert.get('user', 'unknown')}
Asset: {alert.get('asset', 'unknown')}

Respond with ONLY the classification label (one word)."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a SOC analyst. Respond with only the classification label."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )
        result = response.choices[0].message.content.strip().lower()

        # Map common variations
        if "false" in result or "positive" in result:
            return "false_positive"
        elif result in ["false_positive", "low", "medium", "high"]:
            return result
        elif "high" in result:
            return "high"
        elif "medium" in result:
            return "medium"
        elif "low" in result:
            return "low"
        return "medium"
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        return "medium"

def run_episode(difficulty: str, max_steps: int = 200) -> Dict[str, Any]:
    """Run a single episode and return results."""
    # Reset environment
    reset_resp = requests.post(
        f"{API_BASE_URL}/reset",
        json={"difficulty": difficulty},
        timeout=30
    )
    reset_data = reset_resp.json()
    session_id = reset_data.get("session_id")

    if not session_id:
        return {"error": "Failed to reset environment", "score": 0.0}

    observation = reset_data.get("observation", {})
    state = reset_data.get("state", {})
    done = False
    steps = 0

    log_step(0, "reset", f"Started {difficulty} episode with {len(observation.get('alerts', []))} alerts")

    while not done and steps < max_steps:
        alerts = observation.get("alerts", [])
        if not alerts:
            # No more alerts to process
            break

        # Get first unclassified alert
        alert = alerts[0]
        alert_id = alert.get("alert_id")

        # Use LLM for classification
        classification = classify_with_llm(alert)

        action = {
            "action_type": "classify_alert",
            "alert_id": alert_id,
            "classification": classification
        }

        # Execute action
        step_resp = requests.post(
            f"{API_BASE_URL}/step",
            json={"session_id": session_id, "action": action},
            timeout=30
        )
        step_data = step_resp.json()
        observation = step_data.get("observation", {})
        state = step_data.get("state", {})
        done = observation.get("done", False)
        steps += 1

        # Log step
        log_step(steps, f"classify_alert: {classification}",
                f"Alert {alert_id[:8]}... classified as {classification}, reward: {observation.get('reward', 0):.3f}")

        # For medium/hard tasks, also try correlation
        if difficulty in ["medium", "hard"] and steps % 3 == 0 and steps < max_steps - 5:
            # Create incident
            incident_id = f"incident_{steps}"
            action = {
                "action_type": "create_incident",
                "incident_id": incident_id
            }
            requests.post(
                f"{API_BASE_URL}/step",
                json={"session_id": session_id, "action": action},
                timeout=30
            )
            log_step(steps, "create_incident", f"Created incident {incident_id}")

            # Add alert to incident
            if alert_id:
                action = {
                    "action_type": "add_to_incident",
                    "incident_id": incident_id,
                    "alert_id": alert_id
                }
                requests.post(
                    f"{API_BASE_URL}/step",
                    json={"session_id": session_id, "action": action},
                    timeout=30
                )
                steps += 1

    # Get final score from grader
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

def main():
    """Main entry point for inference."""
    log_start()

    # Check health
    print("\nChecking environment health...", file=sys.stderr)
    if not check_health():
        print(f"ERROR: Cannot connect to {API_BASE_URL}", file=sys.stderr)
        log_end({"easy": 0.0, "medium": 0.0, "hard": 0.0})
        sys.exit(1)
    print("Environment is healthy\n", file=sys.stderr)

    # Run all three difficulties
    results = {}
    difficulties = ["easy", "medium", "hard"]

    for difficulty in difficulties:
        print(f"Running {difficulty} task...", file=sys.stderr)
        start_time = time.time()

        try:
            result = run_episode(difficulty)
            results[difficulty] = result["score"]

            elapsed = time.time() - start_time
            print(f"  Score: {result['score']:.4f} in {elapsed:.1f}s\n", file=sys.stderr)
        except Exception as e:
            print(f"  Error: {e}\n", file=sys.stderr)
            results[difficulty] = 0.0

        # Brief pause between tasks
        time.sleep(1)

    # Output final results
    scores = {
        "easy": round(results.get("easy", 0.0), 4),
        "medium": round(results.get("medium", 0.0), 4),
        "hard": round(results.get("hard", 0.0), 4)
    }

    log_end(scores)

    # Also output for parsing
    print("\nFINAL_OUTPUT:")
    print(json.dumps({
        "status": "success",
        "scores": scores,
        "average": round(sum(scores.values()) / 3, 4)
    }))

if __name__ == "__main__":
    main()
