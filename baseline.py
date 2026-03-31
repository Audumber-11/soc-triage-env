"""
SOC Alert Triage Environment - Baseline Agent
OpenEnv Hackathon Submission - Meta PyTorch 2026

This baseline uses OpenAI API to run an agent against all 3 task difficulties.
Required: OPENAI_API_KEY environment variable
"""
import os
import sys
import json
import time
from typing import Dict, Any, List

from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Environment URL (adjust for HF Spaces deployment)
BASE_URL = os.environ.get("ENV_URL", "https://audumber11-soc-triage-env.hf.space")


def classify_with_llm(alert: Dict[str, Any]) -> str:
    """Use LLM to classify a single alert."""
    prompt = f"""You are a SOC analyst. Classify this security alert:

Alert Type: {alert.get('alert_type')}
Source: {alert.get('source')}
Severity: {alert.get('severity')}
Description: {alert.get('description')}
Source IP: {alert.get('source_ip')}
Destination IP: {alert.get('dest_ip')}
User: {alert.get('user')}
Asset: {alert.get('asset')}

Classify as one of: false_positive, low, medium, high
Respond with ONLY the classification label."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a security analyst. Respond with only the classification label."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )

        classification = response.choices[0].message.content.strip().lower()

        # Validate classification
        valid = ["false_positive", "low", "medium", "high"]
        if classification in valid:
            return classification
        elif "false" in classification:
            return "false_positive"
        elif "high" in classification:
            return "high"
        elif "medium" in classification:
            return "medium"
        else:
            return "low"
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        return "low"


def correlate_with_llm(alerts: List[Dict[str, Any]], existing_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use LLM to decide correlation action."""

    alert_summary = "\n".join([
        f"- {a['alert_id']}: {a['alert_type']} from {a['source']} ({a['source_ip']} -> {a['dest_ip']})"
        for a in alerts[:10]  # Limit context
    ])

    incident_summary = "\n".join([
        f"- {i['incident_id']}: {len(i['alerts'])} alerts"
        for i in existing_incidents[:5]
    ]) if existing_incidents else "No existing incidents"

    prompt = f"""You are a SOC analyst correlating security alerts into incidents.

Available Actions:
1. create_incident - Create a new incident
2. add_to_incident - Add alerts to an existing incident (specify incident_id)

Unclassified Alerts:
{alert_summary}

Existing Incidents:
{incident_summary}

Decide the next action. If alerts are related (same IPs, users, or attack pattern), group them.
Respond in JSON format:
{{"action": "create_incident|add_to_incident", "incident_id": "optional", "alert_ids": ["id1", "id2"]}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a security analyst. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        return {"action": "create_incident", "alert_ids": [alerts[0]["alert_id"]] if alerts else []}


def detect_campaign_with_llm(incidents: List[Dict[str, Any]]) -> bool:
    """Use LLM to detect if incidents form a campaign."""
    if len(incidents) < 3:
        return False

    incident_summary = "\n".join([
        f"- {i['incident_id']}: {len(i['alerts'])} alerts"
        for i in incidents[:10]
    ])

    prompt = f"""You are a SOC analyst. Based on these incidents, is there evidence of a coordinated APT campaign?

Incidents:
{incident_summary}

Respond with ONLY "yes" or "no"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a security analyst. Respond with only yes or no."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=10
        )

        return "yes" in response.choices[0].message.content.lower()
    except Exception as e:
        return False


def run_easy_episode() -> float:
    """Run easy task episode."""
    import requests

    # Reset environment
    response = requests.post(f"{BASE_URL}/reset", json={"task_difficulty": "easy"})
    data = response.json()
    session_id = data["session_id"]

    observation = data["observation"]
    alerts_processed = 0

    # Process all alerts
    for step in range(30):
        alerts = observation.get("alerts", [])
        if not alerts:
            break

        for alert in alerts[:5]:  # Process up to 5 per step
            classification = classify_with_llm(alert)

            action = {
                "action_type": "classify_alert",
                "alert_id": alert["alert_id"],
                "classification": classification,
                "confidence": 0.8
            }

            response = requests.post(
                f"{BASE_URL}/step",
                json={"session_id": session_id, "action": action}
            )
            data = response.json()
            observation = data["observation"]
            alerts_processed += 1

            if observation.get("done"):
                break

        if observation.get("done"):
            break

    # Get grader score
    response = requests.post(f"{BASE_URL}/grader", params={"session_id": session_id})
    grader_data = response.json()

    return grader_data.get("score", 0.0)


def run_medium_episode() -> float:
    """Run medium task episode."""
    import requests

    response = requests.post(f"{BASE_URL}/reset", json={"task_difficulty": "medium"})
    data = response.json()
    session_id = data["session_id"]

    observation = data["observation"]
    existing_incidents = []

    for step in range(70):
        alerts = observation.get("alerts", [])
        if not alerts:
            break

        # Use LLM to decide correlation
        decision = correlate_with_llm(alerts, existing_incidents)

        if decision.get("action") == "create_incident":
            # Create new incident
            incident_id = f"incident_{step}"
            action = {
                "action_type": "create_incident",
                "incident_id": incident_id
            }
            requests.post(
                f"{BASE_URL}/step",
                json={"session_id": session_id, "action": action}
            )
            existing_incidents.append({"incident_id": incident_id, "alerts": []})

            # Add alerts to incident
            for alert_id in decision.get("alert_ids", []):
                action = {
                    "action_type": "add_to_incident",
                    "incident_id": incident_id,
                    "alert_id": alert_id
                }
                requests.post(
                    f"{BASE_URL}/step",
                    json={"session_id": session_id, "action": action}
                )

        elif decision.get("action") == "add_to_incident" and decision.get("incident_id"):
            for alert_id in decision.get("alert_ids", []):
                action = {
                    "action_type": "add_to_incident",
                    "incident_id": decision["incident_id"],
                    "alert_id": alert_id
                }
                requests.post(
                    f"{BASE_URL}/step",
                    json={"session_id": session_id, "action": action}
                )

        # Get next observation
        response = requests.post(
            f"{BASE_URL}/step",
            json={"session_id": session_id, "action": {"action_type": "investigate", "alert_id": alerts[0]["alert_id"]}}
        )
        data = response.json()
        observation = data["observation"]
        existing_incidents = observation.get("incidents", [])

        if observation.get("done"):
            break

    # Get grader score
    response = requests.post(f"{BASE_URL}/grader", params={"session_id": session_id})
    grader_data = response.json()

    return grader_data.get("score", 0.0)


def run_hard_episode() -> float:
    """Run hard task episode."""
    import requests

    response = requests.post(f"{BASE_URL}/reset", json={"task_difficulty": "hard"})
    data = response.json()
    session_id = data["session_id"]

    observation = data["observation"]
    existing_incidents = []

    for step in range(160):
        alerts = observation.get("alerts", [])
        if not alerts:
            break

        # Simple strategy: classify and correlate
        for alert in alerts[:3]:
            classification = classify_with_llm(alert)

            # Classify
            requests.post(
                f"{BASE_URL}/step",
                json={
                    "session_id": session_id,
                    "action": {
                        "action_type": "classify_alert",
                        "alert_id": alert["alert_id"],
                        "classification": classification
                    }
                }
            )

            # Investigate high severity
            if classification in ["high", "medium"]:
                requests.post(
                    f"{BASE_URL}/step",
                    json={
                        "session_id": session_id,
                        "action": {
                            "action_type": "investigate",
                            "alert_id": alert["alert_id"]
                        }
                    }
                )

        # Check for campaigns
        if len(existing_incidents) >= 3:
            has_campaign = detect_campaign_with_llm(existing_incidents)
            if has_campaign:
                requests.post(
                    f"{BASE_URL}/step",
                    json={
                        "session_id": session_id,
                        "action": {
                            "action_type": "report_campaign",
                            "campaign_id": f"campaign_detected"
                        }
                    }
                )

        # Create incident for medium/high
        incident_id = f"incident_{step}"
        requests.post(
            f"{BASE_URL}/step",
            json={
                "session_id": session_id,
                "action": {
                    "action_type": "create_incident",
                    "incident_id": incident_id
                }
            }
        )

        for alert in alerts[:2]:
            requests.post(
                f"{BASE_URL}/step",
                json={
                    "session_id": session_id,
                    "action": {
                        "action_type": "add_to_incident",
                        "incident_id": incident_id,
                        "alert_id": alert["alert_id"]
                    }
                }
            )

        response = requests.post(
            f"{BASE_URL}/step",
            json={"session_id": session_id, "action": {"action_type": "investigate", "alert_id": alerts[0]["alert_id"]}}
        )
        data = response.json()
        observation = data["observation"]
        existing_incidents = observation.get("incidents", [])

        if observation.get("done"):
            break

    # Get grader score
    response = requests.post(f"{BASE_URL}/grader", params={"session_id": session_id})
    grader_data = response.json()

    return grader_data.get("score", 0.0)


def main():
    """Run baseline on all 3 difficulties."""
    import requests

    # Check if environment is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(json.dumps({"error": "Environment not accessible", "easy": 0.0, "medium": 0.0, "hard": 0.0}))
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "easy": 0.0, "medium": 0.0, "hard": 0.0}))
        sys.exit(1)

    results = {}

    # Run easy task
    print("Running easy task...", file=sys.stderr)
    try:
        results["easy"] = run_easy_episode()
        print(f"Easy score: {results['easy']}", file=sys.stderr)
    except Exception as e:
        print(f"Easy task failed: {e}", file=sys.stderr)
        results["easy"] = 0.0

    time.sleep(1)

    # Run medium task
    print("Running medium task...", file=sys.stderr)
    try:
        results["medium"] = run_medium_episode()
        print(f"Medium score: {results['medium']}", file=sys.stderr)
    except Exception as e:
        print(f"Medium task failed: {e}", file=sys.stderr)
        results["medium"] = 0.0

    time.sleep(1)

    # Run hard task
    print("Running hard task...", file=sys.stderr)
    try:
        results["hard"] = run_hard_episode()
        print(f"Hard score: {results['hard']}", file=sys.stderr)
    except Exception as e:
        print(f"Hard task failed: {e}", file=sys.stderr)
        results["hard"] = 0.0

    # Output JSON for /baseline endpoint
    print(json.dumps(results))


if __name__ == "__main__":
    main()
