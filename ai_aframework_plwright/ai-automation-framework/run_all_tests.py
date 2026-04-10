#!/usr/bin/env python
"""
Script to run both API and UI tests sequentially
"""
import sys
import subprocess


def run_all_tests():
    """
    Run both API (Pytest) and UI (Behave) tests
    """
    print("=" * 80)
    print("RUNNING ALL TESTS (API + UI)")
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
    ui_result = subprocess.run([sys.executable, "run_bdd_tests.py"])
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    api_status = "✅ PASSED" if api_result.returncode == 0 else "❌ FAILED"
    ui_status = "✅ PASSED" if ui_result.returncode == 0 else "❌ FAILED"
    
    print(f"API Tests (Pytest): {api_status}")
    print(f"UI Tests (Behave):  {ui_status}")
    print("=" * 80)
    
    # Return non-zero if any test suite failed
    if api_result.returncode != 0 or ui_result.returncode != 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
