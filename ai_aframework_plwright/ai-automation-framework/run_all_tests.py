#!/usr/bin/env python
"""
Script to run both API and UI tests sequentially
"""
import os
import sys
import subprocess


def run_all_tests(env="staging"):
    """
    Run both API (Pytest) and UI (Behave) tests

    Args:
        env: Target environment (default: staging)
    """
    os.environ["TEST_ENV"] = env

    print("=" * 80)
    print(f"RUNNING ALL TESTS (API + UI) — env={env}")
    print("=" * 80)
    print()

    # Run API tests first
    print("STEP 1/2: Running API Tests...")
    print("-" * 80)
    api_result = subprocess.run([sys.executable, "run_api_tests.py"])

    print()
    print("=" * 80)

    # Run UI tests
    print("STEP 2/2: Running UI Tests...")
    print("-" * 80)
    ui_result = subprocess.run([sys.executable, "run_bdd_tests.py", f"--env={env}"])

    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    api_status = "PASSED" if api_result.returncode == 0 else "FAILED"
    ui_status = "PASSED" if ui_result.returncode == 0 else "FAILED"

    print(f"API Tests (Pytest): {api_status}")
    print(f"UI Tests (Behave):  {ui_status}")
    print("=" * 80)

    if api_result.returncode != 0 or ui_result.returncode != 0:
        return 1
    return 0


if __name__ == "__main__":
    env_arg = "staging"
    for arg in sys.argv[1:]:
        if arg.startswith("--env="):
            env_arg = arg.split("=", 1)[1]

    exit_code = run_all_tests(env_arg)
    sys.exit(exit_code)
