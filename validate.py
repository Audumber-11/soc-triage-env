"""
Pre-Submission Validation Script
Run this before submitting to ensure all requirements are met.
"""
import requests
import sys
import json

BASE_URL = "http://localhost:8000"


def check_endpoint(endpoint, method="get", data=None, expected_status=200):
    """Check if endpoint returns expected status."""
    try:
        if method == "get":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)

        if response.status_code == expected_status:
            print(f"✓ {endpoint} - OK ({response.status_code})")
            return True, response.json() if response.text else {}
        else:
            print(f"✗ {endpoint} - FAILED ({response.status_code})")
            return False, {}
    except Exception as e:
        print(f"✗ {endpoint} - ERROR: {e}")
        return False, {}


def main():
    print("=" * 60)
    print("SOC Triage Environment - Pre-Submission Validation")
    print("=" * 60)
    print()

    all_passed = True

    # Check health
    print("1. Checking health endpoint...")
    passed, _ = check_endpoint("/health")
    all_passed = all_passed and passed
    print()

    # Check tasks endpoint
    print("2. Checking /tasks endpoint...")
    passed, data = check_endpoint("/tasks")
    if passed:
        tasks = data.get("tasks", [])
        if len(tasks) >= 3:
            print(f"   ✓ Found {len(tasks)} tasks")
            for i, task in enumerate(tasks):
                print(f"     - {task.get('name')} ({task.get('difficulty')})")
        else:
            print(f"   ✗ Expected 3+ tasks, found {len(tasks)}")
            all_passed = False
    all_passed = all_passed and passed
    print()

    # Test reset for each difficulty
    print("3. Testing reset endpoint for all difficulties...")
    session_ids = {}
    for difficulty in ["easy", "medium", "hard"]:
        passed, data = check_endpoint("/reset", "post", {"task_difficulty": difficulty}, 200)
        if passed:
            session_id = data.get("session_id")
            if session_id:
                print(f"   ✓ {difficulty}: session_id={session_id[:8]}...")
                session_ids[difficulty] = session_id
            else:
                print(f"   ✗ {difficulty}: no session_id returned")
                all_passed = False
        else:
            print(f"   ✗ {difficulty}: reset failed")
            all_passed = False
    print()

    # Test step endpoint
    print("4. Testing step endpoint...")
    if "easy" in session_ids:
        action = {
            "action_type": "classify_alert",
            "alert_id": "test_alert",
            "classification": "medium"
        }
        passed, data = check_endpoint("/step", "post", {
            "session_id": session_ids["easy"],
            "action": action
        }, 200)
        if passed:
            print("   ✓ Step executed successfully")
        else:
            print("   ✗ Step failed")
            all_passed = False
    print()

    # Test state endpoint
    print("5. Testing state endpoint...")
    if "easy" in session_ids:
        passed, data = check_endpoint(f"/state/{session_ids['easy']}")
        all_passed = all_passed and passed
    print()

    # Test grader endpoint
    print("6. Testing grader endpoint...")
    if "easy" in session_ids:
        passed, data = check_endpoint(f"/grader?session_id={session_ids['easy']}", "post", {}, 200)
        if passed:
            score = data.get("score")
            if score is not None and 0.0 <= score <= 1.0:
                print(f"   ✓ Grader returned valid score: {score}")
            else:
                print(f"   ✗ Grader returned invalid score: {score}")
                all_passed = False
        all_passed = all_passed and passed
    print()

    # Test baseline endpoint
    print("7. Testing baseline endpoint...")
    passed, data = check_endpoint("/baseline", "post", {}, 200)
    if passed:
        status = data.get("status")
        if status == "success":
            scores = data.get("scores", {})
            print(f"   ✓ Baseline completed: {scores}")
        elif status == "error":
            print(f"   ! Baseline returned error (may need OPENAI_API_KEY): {data.get('error')}")
        else:
            print(f"   ! Baseline status: {status}")
    all_passed = all_passed and passed
    print()

    # Summary
    print("=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Ready for submission!")
    else:
        print("✗ SOME CHECKS FAILED - Fix issues before submitting")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Ensure Dockerfile builds: docker build -t soc-triage-env -f server/Dockerfile .")
    print("2. Deploy to Hugging Face: openenv push --repo-id your-username/soc-triage-env")
    print("3. Verify HF Space returns 200 on /health")
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
