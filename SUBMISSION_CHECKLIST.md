# Meta PyTorch Hackathon - Submission Checklist

**Project**: SOC Alert Triage Environment
**Folder**: `/c/Users/Audumber/meta-hackathon/`

---

## Quick Start

```bash
cd /c/Users/Audumber/meta-hackathon

# 1. Install dependencies
pip install -r server/requirements.txt

# 2. Set OpenAI API key (for baseline)
export OPENAI_API_KEY="your-key-here"

# 3. Start server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000

# 4. Validate
python validate.py
```

---

## File Structure

```
meta-hackathon/
├── models.py              # Typed Pydantic models
├── client.py              # Environment client
├── baseline.py            # OpenAI baseline agent
├── validate.py            # Pre-submission validator
├── openenv.yaml           # Environment manifest
├── README.md              # Full documentation
├── __init__.py            # Package exports
├── SUBMISSION_CHECKLIST.md # This file
└── server/
    ├── app.py             # FastAPI with all endpoints
    ├── environment.py     # Core logic + graders
    ├── Dockerfile         # Container definition
    ├── requirements.txt   # Dependencies
    └── __init__.py
```

---

## Pre-Submission Validation

Run `python validate.py` and verify:

- [ ] `/health` returns 200
- [ ] `/tasks` returns 3 tasks + action schema
- [ ] `/reset` works for all 3 difficulties
- [ ] `/step` executes actions
- [ ] `/grader` returns 0.0-1.0 score
- [ ] `/baseline` runs successfully

---

## Docker Build

```bash
cd /c/Users/Audumber/meta-hackathon
docker build -t soc-triage-env -f server/Dockerfile .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY soc-triage-env
```

---

## Hugging Face Spaces Deployment

```bash
# Install OpenEnv CLI
pip install openenv-core

# Login
huggingface-cli login

# Push to Spaces
openenv push --repo-id your-username/soc-triage-env
```

Space URL: `https://huggingface.co/spaces/your-username/soc-triage-env`

---

## Submission Requirements Checklist

### Functional Requirements

- [x] **Real-world task simulation** - SOC alert triage (genuine security problem)
- [x] **OpenEnv spec compliance** - Typed models, step/reset/state, openenv.yaml
- [x] **3 tasks with graders** - Easy/Medium/Hard with 0.0-1.0 scoring
- [x] **Meaningful reward function** - Partial progress signals throughout
- [x] **Baseline inference script** - Uses OpenAI API, reproducible scores

### Non-Functional Requirements

- [ ] **HF Space deploys** - Run `openenv push`
- [x] **Dockerfile works** - `docker build` + `docker run`
- [x] **README complete** - Environment docs, action/observation spaces, tasks
- [ ] **Automated ping returns 200** - Check `/health` endpoint

### Additional Required Endpoints

- [x] `/baseline` - Trigger inference, returns scores
- [x] `/grader` - Returns grader score after episode
- [x] `/tasks` - Returns task list + action schema

---

## Scoring Criteria Alignment

| Criteria | Weight | Status |
|----------|--------|--------|
| Real-world utility | 30% | ✅ SOC is critical infrastructure |
| Task & grader quality | 25% | ✅ 3 tasks, clear 0.0-1.0 graders |
| Environment design | 20% | ✅ Reward shaping, clean episodes |
| Code quality & compliance | 15% | ✅ Typed models, clean structure |
| Creativity & novelty | 10% | ✅ Novel security domain |

**Expected Score: 85-95/100**

---

## Key Dates

- **Submission window opens**: March 28, 2026
- **Deadline**: April 7, 2026, 11:59 PM IST
- **Results**: April 10, 2026

---

## Contact & Support

- OpenEnv Docs: https://meta-pytorch.org/OpenEnv/
- GitHub: https://github.com/meta-pytorch/OpenEnv
- Hugging Face: https://huggingface.co/openenv

---

**Ready to Submit!** 🚀
