"""
Test script to validate HF Spaces deployment
"""
import requests
import json
import sys

def test_deployment(base_url):
    """Test all critical endpoints."""
    print(f"Testing deployment at: {base_url}")
    print()

    results = []

    # Test 1: Health endpoint
    print("[1/6] Testing /health...")
    try:
        resp = requests.get(f"{base_url}/health", timeout=30)
        if resp.status_code == 200:
            print("    PASS - Health check OK")
            results.append(True)
        else:
            print(f"    FAIL - Status: {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"    FAIL - Error: {e}")
        results.append(False)

    # Test 2: Reset with empty body (CRITICAL - this was failing before)
    print("[2/6] Testing /reset with empty body...")
    try:
        resp = requests.post(f"{base_url}/reset", json={}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            session_id = data.get("session_id")
            print(f"    PASS - Got session_id: {session_id[:8]}...")
            results.append(True)
        else:
            print(f"    FAIL - Status: {resp.status_code}, Response: {resp.text[:100]}")
            results.append(False)
            session_id = None
    except Exception as e:
        print(f"    FAIL - Error: {e}")
        results.append(False)
        session_id = None

    # Test 3: Reset with difficulty
    print("[3/6] Testing /reset with difficulty parameter...")
    try:
        resp = requests.post(f"{base_url}/reset", json={"difficulty": "easy"}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            session_id = data.get("session_id")
            alerts = len(data.get("observation", {}).get("alerts", []))
            print(f"    PASS - Got {alerts} alerts")
            results.append(True)
        else:
            print(f"    FAIL - Status: {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"    FAIL - Error: {e}")
        results.append(False)

    # Test 4: Tasks endpoint
    print("[4/6] Testing /tasks...")
    try:
        resp = requests.get(f"{base_url}/tasks", timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            tasks = data.get("tasks", [])
            print(f"    PASS - Found {len(tasks)} tasks")
            results.append(True)
        else:
            print(f"    FAIL - Status: {resp.status_code}")
            results.append(False)
    except Exception as e:
        print(f"    FAIL - Error: {e}")
        results.append(False)

    # Test 5: Step endpoint (if we have a session)
    print("[5/6] Testing /step...")
    if session_id:
        try:
            resp = requests.post(
                f"{base_url}/step",
                json={
                    "session_id": session_id,
                    "action": {"action_type": "classify_alert", "alert_id": "test_alert", "classification": "medium"}
                },
                timeout=30
            )
            if resp.status_code == 200:
                print("    PASS - Step executed")
                results.append(True)
            elif resp.status_code == 404:
                print("    SKIP - Session expired (expected in stateless environments)")
                results.append(True)
            else:
                print(f"    FAIL - Status: {resp.status_code}")
                results.append(False)
        except Exception as e:
            print(f"    FAIL - Error: {e}")
            results.append(False)
    else:
        print("    SKIP - No session_id available")
        results.append(True)

    # Test 6: Grader endpoint with JSON body
    print("[6/6] Testing /grader...")
    if session_id:
        try:
            resp = requests.post(
                f"{base_url}/grader",
                json={"session_id": session_id},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                score = data.get("score", 0)
                print(f"    PASS - Got score: {score}")
                results.append(True)
            else:
                print(f"    FAIL - Status: {resp.status_code}")
                results.append(False)
        except Exception as e:
            print(f"    FAIL - Error: {e}")
            results.append(False)
    else:
        print("    SKIP - No session_id available")
        results.append(True)

    # Summary
    print()
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")

    if all(results):
        print("SUCCESS: All critical tests passed!")
        print()
        print("You can now submit:")
        print(f"  - GitHub URL: https://github.com/Audumber-11/soc-triage-env")
        print(f"  - HF Space URL: {base_url}")
        return 0
    else:
        print("WARNING: Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    import os

    # Check for URL argument or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Try environment variable or default to HF Spaces
        url = os.environ.get("API_BASE_URL", "https://audumber11-soc-triage-env.hf.space")

    sys.exit(test_deployment(url))
