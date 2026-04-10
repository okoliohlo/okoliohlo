#!/usr/bin/env python
"""
Script to run UI BDD tests using Behave
"""
import sys
import os
import shutil
import yaml
from pathlib import Path

VALID_ENVS = None


def _load_valid_envs():
    """Load valid environment names from environments.yaml"""
    global VALID_ENVS
    if VALID_ENVS is None:
        config_file = Path(__file__).parent / "config" / "environments.yaml"
        with open(config_file, 'r') as f:
            VALID_ENVS = list(yaml.safe_load(f).keys())
    return VALID_ENVS


def clean_allure_reports():
    """Clean Allure report directories"""
    project_root = Path(__file__).parent
    
    dirs_to_clean = [
        project_root / "reports" / "allure-results",
        project_root / "reports" / "allure-report"
    ]
    
    print("Cleaning Allure reports...")
    for directory in dirs_to_clean:
        if directory.exists():
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                print(f"[OK] Cleaned: {directory.name}/")
            except Exception as e:
                print(f"[ERR] Error cleaning {directory.name}/: {e}")
    print("Allure reports cleaned!\n")


def run_ui_tests(args=None, clean_reports=False):
    """
    Run UI BDD tests using Behave
    
    Args:
        args: Additional behave arguments (optional)
    
    Examples:
        python run_bdd_tests.py --env=qa             # Run all UI tests on QA
        python run_bdd_tests.py --env=staging --clean # Clean reports before running
        python run_bdd_tests.py --env=demo --tags=@smoke  # Run smoke tests on demo
        python run_bdd_tests.py --env=local --tags=~@wip  # Exclude WIP tests
        python run_bdd_tests.py --env=qa -f html -o reports/behave-report.html

        #generate allure:
            allure generate reports\allure-results -o reports\allure-report --clean
            allure open reports\allure-report
    """
    # Clean reports if requested
    if clean_reports:
        clean_allure_reports()
    
    # Build behave arguments
    behave_args = [
        "tests/ui/features/",
        "--no-capture",
        "--color",
        "-f", "allure_behave.formatter:AllureFormatter",
        "-o", "reports/allure-results"
    ]
    
    if args:
        behave_args.extend(args)
    
    print("=" * 80)
    print("RUNNING UI TESTS (BEHAVE)")
    print("=" * 80)
    print(f"Behave args: {' '.join(behave_args)}")
    print(f"Python: {sys.executable}")
    print(f"CWD: {os.getcwd()}")
    print("-" * 80)
    
    # Ensure reports directories exist
    os.makedirs("reports/screenshots", exist_ok=True)
    os.makedirs("reports/allure-results", exist_ok=True)
    
    # Import and run behave directly in the same process
    # This allows the debugger to step into behave and step definitions
    try:
        from behave.__main__ import main as behave_main
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        # Set sys.argv for behave
        sys.argv = ['behave'] + behave_args
        
        # Run behave
        exit_code = behave_main()
        
        # Restore original sys.argv
        sys.argv = original_argv
        
        return exit_code if exit_code is not None else 0
        
    except ImportError as e:
        print(f"[ERROR] Could not import behave: {e}")
        print("Please ensure behave is installed: pip install behave")
        return 1
    except SystemExit as e:
        # Behave calls sys.exit(), catch it and return the code
        return e.code if e.code is not None else 0


if __name__ == "__main__":
    # Check for --clean flag
    clean_reports = "--clean" in sys.argv
    
    # Extract --env argument
    env_value = None
    remaining_args = []
    for arg in sys.argv[1:]:
        if arg == "--clean":
            continue
        if arg.startswith("--env="):
            env_value = arg.split("=", 1)[1]
        elif arg == "--env":
            print("[ERROR] --env requires a value, e.g. --env=qa")
            sys.exit(2)
        else:
            remaining_args.append(arg)
    
    if env_value is None:
        valid = _load_valid_envs()
        print(f"[ERROR] --env is required. Valid environments: {', '.join(valid)}")
        print(f"Usage: python run_bdd_tests.py --env=<environment> [options]")
        sys.exit(2)
    
    valid_envs = _load_valid_envs()
    if env_value not in valid_envs:
        print(f"[ERROR] Unknown environment '{env_value}'. Valid: {', '.join(valid_envs)}")
        sys.exit(2)
    
    os.environ["TEST_ENV"] = env_value
    print(f"Environment: {env_value}")
    
    exit_code = run_ui_tests(remaining_args, clean_reports=clean_reports)
    
    print("-" * 80)
    if exit_code == 0:
        print("[PASS] UI TESTS PASSED")
    else:
        print("[FAIL] UI TESTS FAILED")
    print("=" * 80)
    
    sys.exit(exit_code)
