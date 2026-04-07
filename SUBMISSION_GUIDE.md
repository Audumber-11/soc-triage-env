# Hackathon Submission Guide

## Problem Fixed

Your original submission was failing Phase 1 with:
```
{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}
```

**Root Cause**: The OpenEnv validator sends a POST request to `/reset` with an empty or minimal body, but your endpoint required a mandatory body parameter.

**Fix Applied**: Modified `/reset` endpoint to:
- Accept empty body (defaults to "easy")
- Accept both `difficulty` and `task_difficulty` field names
- Use FastAPI's `Request` object for flexible parsing

## Changes Made

### 1. Fixed `server/app.py`
- `/reset` endpoint now accepts empty body and optional parameters
- `/grader` endpoint now accepts both query params and JSON body
- Fixed syntax errors in baseline endpoint
- Added proper error handling

### 2. Created proper `inference.py`
- Uses OpenAI Client with configurable `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
- Outputs structured logs with `[START]`, `[STEP]`, `[END]` markers
- Returns JSON scores for easy, medium, hard tasks

### 3. Updated `Dockerfile`
- Configured for HF Spaces (port 7860)
- Single worker for session persistence
- Proper file copying

### 4. Updated `openenv.yaml`
- Changed port from 8000 to 7860 (HF Spaces standard)
- Updated author name

### 5. Added deployment tools
- `deploy.py` - Upload to HF Spaces with token
- `test_deployment.py` - Validate all endpoints

## Deployment Steps

### Step 1: Get Hugging Face Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with "write" access
3. Copy the token

### Step 2: Deploy to HF Spaces
```bash
cd C:/Users/Audumber/meta-hackathon

# Set your token (Windows)
set HF_TOKEN=your_token_here

# Run deployment script
python deploy.py
```

Or manually upload:
```bash
# Install huggingface_hub
pip install huggingface_hub

# Login
huggingface-cli login

# Upload
huggingface-cli upload audumber11/soc-triage-env . --repo-type=space --commit-message="Fix OpenEnv compliance"
```

### Step 3: Wait for Build
After upload, HF Spaces will build the Docker image. This takes 5-10 minutes.
Monitor at: https://huggingface.co/spaces/audumber11/soc-triage-env

### Step 4: Test Deployment
```bash
# Set the URL
set API_BASE_URL=https://audumber11-soc-triage-env.hf.space

# Run tests
python test_deployment.py
```

Or manually test:
```bash
# Test health
curl https://audumber11-soc-triage-env.hf.space/health

# Test reset (this was failing before)
curl -X POST https://audumber11-soc-triage-env.hf.space/reset -H "Content-Type: application/json" -d '{}'

# Test with difficulty
curl -X POST https://audumber11-soc-triage-env.hf.space/reset -H "Content-Type: application/json" -d '{"difficulty":"easy"}'
```

### Step 5: Submit
Once tests pass, submit to the hackathon with these URLs:

- **GitHub URL**: https://github.com/Audumber-11/soc-triage-env
- **HF Space URL**: https://huggingface.co/spaces/audumber11/soc-triage-env

## Validation Checklist

- [ ] `/health` returns 200 OK
- [ ] `/reset` with empty body returns 200 OK
- [ ] `/reset` with `{"difficulty":"easy"}` returns 200 OK
- [ ] `/tasks` returns 3 tasks
- [ ] `/step` executes successfully
- [ ] `/grader` returns score between 0.0-1.0
- [ ] Docker builds successfully on HF Spaces
- [ ] Space shows "Running" status

## Local Testing (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000

# Run tests
python test_deployment.py http://localhost:8000
```

## Files Changed

```
server/app.py          - Fixed reset/grader endpoints
inference.py           - Created proper inference script
Dockerfile             - Updated for HF Spaces (port 7860)
openenv.yaml           - Updated port to 7860
README.md              - Updated documentation
```

## Support

If you encounter issues:
1. Check HF Spaces build logs: https://huggingface.co/spaces/audumber11/soc-triage-env
2. Run local tests: `python test_deployment.py`
3. Check environment variables are set correctly
4. Ensure OpenAI API key is valid (for inference)

## Links

- **GitHub**: https://github.com/Audumber-11/soc-triage-env
- **HF Space**: https://huggingface.co/spaces/audumber11/soc-triage-env
- **Hackathon Dashboard**: https://www.scaler.com/school-of-technology/meta-pytorch-hackathon/dashboard
