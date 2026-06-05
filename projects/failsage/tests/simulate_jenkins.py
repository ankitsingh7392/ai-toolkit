#!/usr/bin/env python3
"""
Simulates Jenkins sending test results to the FailSage.

Usage:
    python simulate_jenkins.py              # Single run
    python simulate_jenkins.py --runs=5     # Multiple runs (stress test)
    python simulate_jenkins.py --poll       # Send and poll until complete
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

BASE_URL = "http://localhost:8000"

SAMPLE_XML = (Path(__file__).parent / "sample_junit.xml").read_text()

BRANCHES = ["main", "feature/auth-refactor", "fix/payment-timeout", "release/2.4.0"]
JOBS = ["backend-regression", "api-integration", "ui-smoke", "full-regression"]
ENVS = ["staging", "qa", "preview"]
COMMITS = [
    "a3f8c21d9e04b15fce3d0a71b8e29c4f056d7813",
    "7b2e4f9d1c06a38b25f74c8e0d19b3a5c642891f",
    "c9a1b7e3d4f20c58a6b3e7d0f9c21b4a8e365027",
    "2d5f8a1c3e09b27f4a6d8e1b0c3f5a7d921483b6",
]


def send_run(build_id: str, branch: str, commit: str, job: str, env: str) -> dict:
    payload = {
        "ci": {
            "build_id": build_id,
            "job_name": job,
            "git_commit": commit,
            "branch": branch,
            "environment": env,
            "jenkins_url": f"https://jenkins.example.com/job/{job}/{build_id}/",
        },
        "junit_xml": SAMPLE_XML,
        "bug_description": None,
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(f"{BASE_URL}/ci/jenkins/test-results", json=payload)
        resp.raise_for_status()
        return resp.json()


def poll_run(run_id: str, max_wait: int = 120) -> dict:
    print(f"  Polling run {run_id}…", end="", flush=True)
    start = time.time()
    with httpx.Client(timeout=10) as client:
        while time.time() - start < max_wait:
            r = client.get(f"{BASE_URL}/runs/{run_id}")
            r.raise_for_status()
            data = r.json()
            status = data["status"]
            if status in ("completed", "failed"):
                print(f" {status.upper()}")
                return data
            print(".", end="", flush=True)
            time.sleep(3)
    print(" TIMEOUT")
    return {}


def print_summary(run: dict) -> None:
    print("\n── Build Summary ──────────────────────────────────────")
    print(f"  Job:       {run['job_name']} #{run['build_id']}")
    print(f"  Branch:    {run['branch']}")
    print(f"  Tests:     {run['total_tests']} total | {run['passed_tests']} passed | {run['failed_tests']} failed")
    print(f"  Risk:      {'⚠ ' + run.get('risk_level', '?') if run.get('build_at_risk') else '✓ OK'}")
    if run.get("build_insight"):
        insight = run["build_insight"]
        print(f"  Action:    {insight.get('recommended_action', '?')}")
        print(f"  Rationale: {insight.get('risk_rationale', '')[:100]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jenkins payload simulator")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs to simulate")
    parser.add_argument("--poll", action="store_true", help="Wait for analysis to complete")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend URL")
    args = parser.parse_args()

    print(f"FailSage — Jenkins Simulator")
    print(f"Target: {args.base_url}")
    print(f"Sending {args.runs} run(s)…\n")

    for i in range(args.runs):
        build_id = str(1000 + i + random.randint(0, 99))
        branch = random.choice(BRANCHES)
        commit = random.choice(COMMITS)
        job = random.choice(JOBS)
        env = random.choice(ENVS)

        print(f"[{i+1}/{args.runs}] {job} #{build_id} ({branch}) → ", end="", flush=True)

        try:
            result = send_run(build_id, branch, commit, job, env)
            run_id = result["run_id"]
            print(f"run_id={run_id} [{result['status']}]")
            print(f"  Poll URL: {BASE_URL}{result['polling_url']}")
            print(f"  Failures: {BASE_URL}/failures/{run_id}")

            if args.poll or args.runs == 1:
                run_data = poll_run(run_id)
                if run_data:
                    print_summary(run_data)

        except httpx.ConnectError:
            print(f"\n✗ Cannot connect to {args.base_url}. Is the backend running?")
            print("  Run: make up")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP {e.response.status_code}: {e.response.text[:200]}")

        if i < args.runs - 1:
            time.sleep(0.5)

    print("\nDone. Open http://localhost:3000 to see results.")


if __name__ == "__main__":
    main()
