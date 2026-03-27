---
title: SOC Alert Triage
emoji: 🛡️
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---

# SOC Alert Triage Environment

OpenEnv for training AI agents on security alert triage, incident correlation, and APT campaign detection.

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
