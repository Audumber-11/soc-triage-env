"""
Comprehensive Pre-Submission Validation Script
Tests all requirements without needing the server to be running.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "server"))

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_check(name, status, details=""):
    """Print check result."""
    symbol = "PASS" if status else "FAIL"
    print(f"  [{symbol}] {name}")
    if details:
        print(f"      {details}")
    return status

def check_file_exists(filepath, description):
    """Check if file exists."""
    path = Path(filepath)
    exists = path.exists()
    return print_check(f"{description}: {filepath}", exists,
                      f"Found ({path.absolute()})" if exists else "NOT FOUND")

def check_openenv_yaml():
    """Validate openenv.yaml structure."""
    print_header("CHECK 1: OpenEnv Spec Compliance - openenv.yaml")

    try:
        import yaml
        with open("openenv.yaml", "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print_check("openenv.yaml parsing", False, str(e))
        return False

    required_fields = [
        ("name", str),
        ("version", str),
        ("description", str),
    ]

    all_pass = True
    for field, field_type in required_fields:
        if field in config:
            print_check(f"Field '{field}' present", True)
        else:
            print_check(f"Field '{field}' present", False, "Missing")
            all_pass = False

    # Check tasks
    if "tasks" in config:
        tasks = config["tasks"]
        print_check(f"Tasks defined", len(tasks) >= 3,
                   f"Found {len(tasks)} tasks" if len(tasks) >= 3 else f"Need 3+ tasks, found {len(tasks)}")

        for diff in ["easy", "medium", "hard"]:
            if diff in tasks:
                print_check(f"  - {diff} task present", True)
            else:
                print_check(f"  - {diff} task present", False)
                all_pass = False
    else:
        print_check("Tasks section", False, "Missing")
        all_pass = False

    return all_pass

def check_typed_models():
    """Check typed Pydantic models."""
    print_header("CHECK 2: Typed Models (Pydantic)")

    try:
        from models import (
            TaskDifficulty, AlertSeverity, AlertSource,
            SecurityAlert, TriageAction, TriageObservation,
            TriageState, TaskConfig, Incident, Campaign
        )
        print_check("All models importable", True)
    except Exception as e:
        print_check("All models importable", False, str(e))
        return False

    # Check model fields
    checks = [
        (SecurityAlert, ["alert_id", "timestamp", "source", "severity", "ground_truth"]),
        (TriageAction, ["action_type"]),
        (TriageObservation, ["alerts", "done", "reward"]),
        (TriageState, ["episode_id", "step_count", "current_score"]),
    ]

    all_pass = True
    for model, fields in checks:
        for field in fields:
            has_field = hasattr(model, "__fields__") and field in model.__fields__
            if not has_field and hasattr(model, "model_fields"):
                has_field = field in model.model_fields

            status = print_check(f"{model.__name__}.{field}", has_field)
            all_pass = all_pass and status

    return all_pass

def check_environment_methods():
    """Check environment has required methods."""
    print_header("CHECK 3: Environment Methods (reset/step/state)")

    try:
        from server.environment import SOCTriageEnvironment
        env = SOCTriageEnvironment()

        methods = ["reset", "step", "state"]
        all_pass = True
        for method in methods:
            has_method = hasattr(env, method) and callable(getattr(env, method))
            print_check(f"SOCTriageEnvironment.{method}()", has_method)
            all_pass = all_pass and has_method

        # Check grader methods
        grader_methods = ["_calculate_easy_score", "_calculate_medium_score",
                         "_calculate_hard_score", "_calculate_score"]
        for method in grader_methods:
            has_method = hasattr(env, method)
            print_check(f"Grader method: {method}", has_method)
            all_pass = all_pass and has_method

        return all_pass
    except Exception as e:
        print_check("Environment instantiation", False, str(e))
        return False

def check_dockerfile():
    """Check Dockerfile exists and is valid."""
    print_header("CHECK 4: Dockerfile")

    dockerfile_path = Path("server/Dockerfile")
    exists = dockerfile_path.exists()
    print_check("Dockerfile exists", exists, str(dockerfile_path.absolute()))

    if not exists:
        return False

    with open(dockerfile_path, encoding='utf-8') as f:
        content = f.read()

    required = ["FROM", "WORKDIR", "COPY", "EXPOSE", "CMD"]
    all_pass = True
    for req in required:
        present = req in content
        print_check(f"Contains {req}", present)
        all_pass = all_pass and present

    # Check port 8000
    port_present = "8000" in content or "${PORT}" in content
    print_check("Port 8000 exposed", port_present)
    all_pass = all_pass and port_present

    return all_pass

def check_baseline_script():
    """Check baseline script exists and is valid."""
    print_header("CHECK 5: Baseline Script")

    baseline_path = Path("baseline.py")
    exists = baseline_path.exists()
    print_check("baseline.py exists", exists)

    if not exists:
        return False

    with open(baseline_path, encoding='utf-8') as f:
        content = f.read()

    checks = [
        ("Imports OpenAI", "openai" in content),
        ("Uses GPT-4o-mini", "gpt-4o-mini" in content),
        ("Handles all difficulties", "easy" in content and "medium" in content and "hard" in content),
        ("run_easy_episode function", "def run_easy_episode" in content),
        ("run_medium_episode function", "def run_medium_episode" in content),
        ("run_hard_episode function", "def run_hard_episode" in content),
    ]

    all_pass = True
    for name, present in checks:
        print_check(name, present)
        all_pass = all_pass and present

    return all_pass

def check_server_endpoints():
    """Check server has required endpoints."""
    print_header("CHECK 6: Server Endpoints")

    try:
        from server.app import app
        routes = [route.path for route in app.routes]

        required_endpoints = [
            "/reset", "/step", "/state/{session_id}",
            "/tasks", "/grader", "/baseline", "/health"
        ]

        all_pass = True
        for endpoint in required_endpoints:
            # Check if endpoint exists (may be with or without parameters)
            found = any(endpoint.replace("{session_id}", "").rstrip("/") in r or
                       endpoint.format(session_id="") in r for r in routes)
            # Also check for exact match
            found = found or endpoint in routes
            print_check(f"Endpoint {endpoint}", found)
            all_pass = all_pass and found

        print(f"\n  Available routes: {', '.join(routes)}")
        return all_pass
    except Exception as e:
        print_check("Server import", False, str(e))
        return False

def check_tasks_and_graders():
    """Check tasks and graders return 0.0-1.0 scores."""
    print_header("CHECK 7: Tasks and Graders")

    try:
        from server.environment import SOCTriageEnvironment
        from models import TaskDifficulty

        difficulties = [
            (TaskDifficulty.EASY, "_calculate_easy_score"),
            (TaskDifficulty.MEDIUM, "_calculate_medium_score"),
            (TaskDifficulty.HARD, "_calculate_hard_score"),
        ]

        all_pass = True
        for diff, score_method in difficulties:
            env = SOCTriageEnvironment()
            env.reset(diff)

            score = getattr(env, score_method)()
            in_range = 0.0 <= score <= 1.0

            print_check(f"{diff.value} grader returns 0.0-1.0", in_range,
                       f"Score: {score}")
            all_pass = all_pass and in_range

        return all_pass
    except Exception as e:
        print_check("Task/Grader test", False, str(e))
        return False

def check_hf_spaces_config():
    """Check HF Spaces deployment configuration."""
    print_header("CHECK 8: Hugging Face Spaces Configuration")

    # Check app.py exists
    hf_config = Path("server/app.py").exists()
    print_check("server/app.py exists", hf_config)

    # Check openenv.yaml has HF config
    try:
        import yaml
        with open("openenv.yaml", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        has_hf = "app_port" in config or "app_file" in config or "hf_spaces" in str(config)
        print_check("HF Spaces config in openenv.yaml", has_hf)
    except:
        print_check("HF Spaces config in openenv.yaml", False, "Cannot parse")
        has_hf = False

    return hf_config and has_hf

def check_readme():
    """Check README is complete."""
    print_header("CHECK 9: README Documentation")

    readme_path = Path("README.md")
    exists = readme_path.exists()
    print_check("README.md exists", exists)

    if not exists:
        return False

    with open(readme_path, encoding='utf-8') as f:
        content = f.read()

    required_sections = [
        ("Overview/Description", "overview" in content.lower() or "description" in content.lower()),
        ("Tasks section", "task" in content.lower()),
        ("Action Space", "action" in content.lower()),
        ("Observation Space", "observation" in content.lower()),
        ("Installation/Setup", "install" in content.lower() or "setup" in content.lower()),
        ("Docker instructions", "docker" in content.lower()),
    ]

    all_pass = True
    for name, present in required_sections:
        print_check(f"README has {name}", present)
        all_pass = all_pass and present

    return all_pass

def generate_summary(results):
    """Generate validation summary."""
    print_header("VALIDATION SUMMARY")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print(f"\n  Passed: {passed}/{total}")
    print(f"  Failed: {total - passed}/{total}")

    print("\n  Results by check:")
    for name, result in results.items():
        symbol = "OK" if result else "XX"
        print(f"    [{symbol}] {name}")

    if passed == total:
        print("\n" + "=" * 70)
        print("  ALL CHECKS PASSED - Ready for submission!")
        print("=" * 70)
        print("\n  Next steps:")
        print("    1. Deploy to HF Spaces: openenv push --repo-id your-username/soc-triage-env")
        print("    2. Verify /health returns 200 on deployed Space")
        print("    3. Run /baseline to verify scores")
        print("    4. Submit your entry!")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  SOME CHECKS FAILED - Fix issues before submitting")
        print("=" * 70)
        return 1

def main():
    """Run all validation checks."""
    print("\n" + "=" * 70)
    print("  SOC Triage Environment - Pre-Submission Validation")
    print("  Meta PyTorch Hackathon 2026")
    print("=" * 70)

    results = {}

    # Run all checks
    results["OpenEnv YAML"] = check_openenv_yaml()
    results["Typed Models"] = check_typed_models()
    results["Environment Methods"] = check_environment_methods()
    results["Dockerfile"] = check_dockerfile()
    results["Baseline Script"] = check_baseline_script()
    results["Server Endpoints"] = check_server_endpoints()
    results["Tasks & Graders"] = check_tasks_and_graders()
    results["HF Spaces Config"] = check_hf_spaces_config()
    results["README"] = check_readme()

    return generate_summary(results)

if __name__ == "__main__":
    sys.exit(main())
