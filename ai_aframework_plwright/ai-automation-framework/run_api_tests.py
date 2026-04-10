#!/usr/bin/env python
"""
Script to run API tests using Pytest
"""
import sys
import subprocess
import os


def run_api_tests(args=None):
    """
    Run API tests using Pytest
    
    Args:
        args: Additional pytest arguments (optional)
    
    Examples:
        python run_api_tests.py                    # Run all API tests
        python run_api_tests.py -m smoke           # Run smoke tests only
        python run_api_tests.py -m "api and not slow"  # API tests excluding slow
        python run_api_tests.py -v                 # Verbose output
        python run_api_tests.py -n auto            # Parallel execution
    """
    cmd = [
        "pytest",
        "tests/api/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    if args:
        cmd.extend(args)
    
    print("=" * 80)
    print("RUNNING API TESTS (PYTEST)")
    print("=" * 80)
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)
    
    # Ensure reports directory exists
    os.makedirs("reports/logs", exist_ok=True)
    
    result = subprocess.run(cmd, cwd=".")
    return result.returncode


if __name__ == "__main__":
    # Pass any additional arguments to pytest
    additional_args = sys.argv[1:] if len(sys.argv) > 1 else []
    exit_code = run_api_tests(additional_args)
    
    print("-" * 80)
    if exit_code == 0:
        print("✅ API TESTS PASSED")
    else:
        print("❌ API TESTS FAILED")
    print("=" * 80)
    
    sys.exit(exit_code)
