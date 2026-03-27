---
title: SOC Alert Triage Environment
emoji: 🛡️
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
license: mit
short_description: OpenEnv for training AI agents on SOC alert triage
---

# SOC Alert Triage Environment

**OpenEnv Hackathon Submission - Meta PyTorch 2026**

A realistic Security Operations Center (SOC) environment for training AI agents on security alert triage, incident correlation, and Advanced Persistent Threat (APT) campaign detection.

## Tasks

- **Easy**: Basic Alert Classification (20 alerts)
- **Medium**: Multi-Source Incident Correlation (50 alerts)
- **Hard**: APT Campaign Detection (200 alerts over 30 days)

## Quick Start

```python
from client import SOCTriageClient

client = SOCTriageClient()
client.reset(task_difficulty="easy")

# Get current alerts
state = client.get_state()
print(state["alerts"])

# Take action
result = client.step({
    "action_type": "classify_alert",
    "alert_id": "alert_001",
    "classification": "high"
})
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tasks` | GET | Get task definitions |
| `/reset` | POST | Start new episode |
| `/step` | POST | Execute action |
| `/state/{id}` | GET | Get current state |

## License

MIT License
