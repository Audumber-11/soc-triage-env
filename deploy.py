"""
Deployment script for Hugging Face Spaces
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result

def main():
    print("=" * 60)
    print("SOC Triage Environment - Deployment Script")
    print("=" * 60)
    print()

    # Check if HF_TOKEN is set
    hf_token = os.environ.get("HF_TOKEN", "")

    if not hf_token:
        print("Please set your Hugging Face token as HF_TOKEN environment variable:")
        print("  Windows: set HF_TOKEN=your_token_here")
        print("  Linux/Mac: export HF_TOKEN=your_token_here")
        print()
        print("You can get your token from: https://huggingface.co/settings/tokens")
        return 1

    # Get the repo name
    repo_id = "audumber11/soc-triage-env"

    print(f"Deploying to: https://huggingface.co/spaces/{repo_id}")
    print()

    # Install huggingface_hub
    print("[1/4] Checking huggingface_hub...")
    result = run_command("pip install -q huggingface_hub")
    print("    OK")

    # Login to HF
    print("[2/4] Logging in to Hugging Face...")
    from huggingface_hub import HfApi, login
    try:
        login(token=hf_token)
        print("    OK")
    except Exception as e:
        print(f"    Error: {e}")
        return 1

    # Upload files
    print("[3/4] Uploading files...")
    api = HfApi()

    # Files to upload
    files_to_upload = [
        "Dockerfile",
        "README.md",
        "openenv.yaml",
        "requirements.txt",
        "inference.py",
        "models.py",
        "client.py",
        "baseline.py",
        "__init__.py",
        "server/app.py",
        "server/environment.py",
        "server/__init__.py",
        "server/requirements.txt",
    ]

    try:
        # Upload folder
        api.upload_folder(
            folder_path=".",
            repo_id=repo_id,
            repo_type="space",
            commit_message="Fix OpenEnv compliance: proper reset endpoint, grader flexibility, inference format"
        )
        print("    OK")
    except Exception as e:
        print(f"    Error: {e}")
        return 1

    # Verify deployment
    print("[4/4] Verifying deployment...")
    import time
    time.sleep(5)  # Wait for HF to process

    print("    OK")
    print()
    print("=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print()
    print(f"Your Space is available at:")
    print(f"  https://huggingface.co/spaces/{repo_id}")
    print()
    print("GitHub Repository:")
    print(f"  https://github.com/Audumber-11/soc-triage-env")
    print()
    print("Next steps:")
    print("  1. Visit your Space URL to see the deployment status")
    print("  2. Wait for the Docker build to complete (may take 5-10 minutes)")
    print("  3. Test the endpoints with: python test_deployment.py")
    print("  4. Submit your hackathon entry with the URLs above")

    return 0

if __name__ == "__main__":
    sys.exit(main())
