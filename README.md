---
title: SOC Alert Triage
emoji: 🔒
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---

# SOC Alert Triage Environment

OpenEnv for training AI agents on security alert triage, incident correlation, and APT campaign detection.

## Overview

This environment simulates a real Security Operations Center (SOC) where AI agents learn to:
- Classify security alerts as false_positive/low/medium/high
- Correlate related alerts into security incidents
- Detect Advanced Persistent Threat (APT) campaigns
- Recommend appropriate response actions

## Task Difficulties

### Easy: Basic Alert Classification
- Classify 20 security alerts
- Max 25 steps
- Target score: 0.85

### Medium: Multi-Source Incident Correlation  
- Correlate 50 alerts into incidents
- Max 60 steps
- Target score: 0.75

### Hard: APT Campaign Detection
- Detect APT campaigns in 200 noisy alerts over 30 days
- Max 150 steps
- Target score: 0.65

## Action Space

| Action | Parameters | Description |
|--------|------------|-------------|
| classify_alert | alert_id, classification | Classify alert severity |
| create_incident | incident_id | Create new incident |
| add_to_incident | alert_id, incident_id | Add alert to incident |
| set_root_cause | incident_id, root_cause | Identify root cause |
| investigate | alert_id | Deep investigation |
| escalate | incident_id | Escalate to senior analyst |
| report_campaign | campaign_id, incident_ids | Report APT campaign |
| set_response | incident_id, response_action | Set response action |

## Observation Space

- List of current security alerts
- List of created incidents
- List of detected campaigns
- Investigation results
- Reward and done flags

## Quick Start

```python
from client import SOCTriageClient

client = SOCTriageClient()
client.reset(task_difficulty="easy")
state = client.get_state()
```

## API

- `GET /health` - Health check
- `GET /tasks` - Get tasks
- `POST /reset` - Start episode
- `POST /step` - Take action
- `GET /state/{session_id}` - Get state
- `POST /grader?session_id=xxx` - Get score
- `POST /baseline` - Run baseline agent

## Setup

```bash
pip install -r requirements.txt
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Environment Variables

- `API_BASE_URL` - Environment URL (default: http://localhost:8000)
- `MODEL_NAME` - Model for inference (default: gpt-4o-mini)
- `OPENAI_API_KEY` - OpenAI API key for LLM calls
