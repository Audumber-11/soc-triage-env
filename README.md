---
title: SOC Alert Triage
emoji: 🔒
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---

# SOC Alert Triage Environment

**OpenEnv Hackathon Submission - Meta PyTorch 2026**

An OpenEnv environment for training AI agents on security alert triage, incident correlation, and APT campaign detection.

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
- `POST /reset` - Start episode (accepts empty body, defaults to easy)
- `POST /step` - Take action
- `GET /state/{session_id}` - Get state
- `POST /grader` - Get score (accepts query params or JSON body)
- `POST /baseline` - Run baseline agent

## Local Setup

```bash
pip install -r requirements.txt
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Environment Variables

- `API_BASE_URL` - Environment URL (default: http://localhost:8000)
- `MODEL_NAME` - Model for inference (default: gpt-4o-mini)
- `OPENAI_API_KEY` - OpenAI API key for LLM calls
- `HF_TOKEN` - HuggingFace token (for upload)

## Deployment to Hugging Face Spaces

1. Install Hugging Face CLI:
```bash
pip install huggingface_hub
```

2. Login to Hugging Face:
```bash
huggingface-cli login
```

3. Create a new Space (if not exists):
```bash
huggingface-cli repo create soc-triage-env --type space --sdk docker
```

4. Push to Hugging Face:
```bash
git add .
git commit -m "Fix OpenEnv compliance issues"
git push
```

## Validation

Run the pre-submission check:
```bash
python -c "
import requests
import json

BASE_URL = 'http://localhost:8000'

# Test health
print('Testing /health...')
resp = requests.get(f'{BASE_URL}/health')
assert resp.status_code == 200, 'Health check failed'
print('✓ Health OK')

# Test reset with empty body (the critical fix)
print('Testing /reset with empty body...')
resp = requests.post(f'{BASE_URL}/reset', json={})
assert resp.status_code == 200, f'Reset failed: {resp.text}'
data = resp.json()
assert 'session_id' in data, 'Missing session_id'
print('✓ Reset with empty body OK')

# Test grader
print('Testing /grader...')
session_id = data['session_id']
resp = requests.post(f'{BASE_URL}/grader', json={'session_id': session_id})
assert resp.status_code == 200, 'Grader failed'
print('✓ Grader OK')

print('\n✅ All validation tests passed!')
"
```

## Inference Script

The `inference.py` script:
- Uses OpenAI Client for LLM calls
- Emits structured logs with [START], [STEP], and [END] markers
- Outputs JSON scores for easy, medium, hard tasks
- Runs in under 20 minutes

Run locally:
```bash
export OPENAI_API_KEY="your-key"
export API_BASE_URL="http://localhost:8000"
python inference.py
```

## Project Structure

```
├── server/
│   ├── app.py           # FastAPI application
│   ├── environment.py   # Environment logic
│   └── requirements.txt # Dependencies
├── models.py            # Pydantic models
├── client.py            # Environment client
├── inference.py         # Baseline inference script
├── baseline.py          # Baseline agent implementation
├── Dockerfile           # Docker configuration
├── openenv.yaml         # OpenEnv configuration
└── README.md            # This file
```

## License

MIT License
