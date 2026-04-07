#!/bin/bash
# Upload script for HF Spaces

# Install huggingface_hub if not installed
pip install -q huggingface_hub

# Login with token (user will need to provide token)
echo "Please login to Hugging Face: " 
huggingface-cli login

# Upload to Spaces using upload folder
huggingface-cli upload audumber11/soc-triage-env . --repo-type=space --commit-message="Fix OpenEnv compliance"

echo "Upload complete!"
echo "Check your space at: https://huggingface.co/spaces/audumber11/soc-triage-env"
