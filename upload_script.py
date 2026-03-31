import os
from huggingface_hub import upload_folder

# Set your HF token here
os.environ['HF_TOKEN'] = 'your_hf_token_here'
repo_id = "audumber11/soc-triage-env"

upload_folder(
    repo_id=repo_id,
    repo_type="space",
    folder_path=".",
    path_in_repo="",
    ignore_patterns=["**/__pycache__/**", "**/*.pyc", ".git/**", ".gitignore", "tests/**", "scripts/**", "configs/**", "docker/**", "src/**", "pre_submission_check.py", "validate.py", "SUBMISSION_CHECKLIST.md", "upload_script.py"],
)
print("Re-upload complete!")
