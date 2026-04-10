"""
PyInvoke Tasks for Test Automation Framework
Run tasks with: invoke <task-name>
List all tasks: invoke --list
"""

from invoke import task
import os
import shutil
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
REPORTS_DIR = PROJECT_ROOT / "reports"
ALLURE_RESULTS_DIR = REPORTS_DIR / "allure-results"
ALLURE_REPORT_DIR = REPORTS_DIR / "allure-report"


# ============================================================================
# Test Execution Tasks
# ============================================================================

@task
def test_smoke(c, env="staging"):
    """
    Run smoke tests (API + UI)
    Usage:
        invoke test-smoke                # Run smoke tests (staging)
        invoke test-smoke --env=qa       # Run smoke tests against QA
    """
    os.environ["TEST_ENV"] = env
    
    print("=" * 80)
    print("RUNNING SMOKE TESTS")
    print(f"Environment: {env}")
    print("=" * 80)
    
    # Run API smoke tests
    print("\n[1/2] Running API smoke tests...")
    c.run(
        "python -m pytest tests/api/ -m smoke -v --tb=short",
        pty=False
    )
    
    # Run UI smoke tests
    print("\n[2/2] Running UI smoke tests...")
    c.run(
        "python run_bdd_tests.py --tags=@smoke",
        pty=False
    )
    
    print("\n" + "=" * 80)
    print("✅ SMOKE TESTS COMPLETED")
    print("=" * 80)


@task
def test_api(c, marker="", verbose=True):
    """
    Run API tests (pytest)
    Usage: 
        invoke test-api                    # Run all API tests
        invoke test-api --marker=smoke     # Run API smoke tests
        invoke test-api --marker=integration  # Run integration tests
    """
    print("=" * 80)
    print("RUNNING API TESTS")
    print("=" * 80)
    
    cmd = "python -m pytest tests/api/"
    
    if marker:
        cmd += f" -m {marker}"
    
    if verbose:
        cmd += " -v"
    
    cmd += " --tb=short --color=yes"
    
    print(f"\nCommand: {cmd}\n")
    c.run(cmd, pty=False)
    
    print("\n" + "=" * 80)
    print("✅ API TESTS COMPLETED")
    print("=" * 80)


@task
def test_demo(c, headless=False, env="demo"):
    """
    Run the demo UI test (Contact page button validation)
    Usage:
        invoke test-demo                # Run demo in headed mode
        invoke test-demo --headless     # Run demo in headless mode
        invoke test-demo --env=demo     # Run demo
    """
    os.environ["TEST_ENV"] = env
    
    print("=" * 80)
    print("RUNNING DEMO TEST — Contact page validation")
    print(f"Environment: {env}")
    print("=" * 80)
    
    cmd = "python run_bdd_tests.py --tags=@demo"
    
    if headless:
        os.environ["HEADLESS"] = "true"
    
    print(f"\nCommand: {cmd}\n")
    c.run(cmd, pty=False)
    
    print("\n" + "=" * 80)
    print("✅ DEMO TEST COMPLETED")
    print("=" * 80)


@task
def test_ui(c, tags="@tc01", headless=False, env="staging"):
    """
    Run UI tests (Behave/BDD)
    Usage:
        invoke test-ui                     # Run all UI tests
        invoke test-ui --tags=@smoke       # Run UI smoke tests
        invoke test-ui --tags=@tc01        # Run specific test case
        invoke test-ui --headless          # Run in headless mode
        invoke test-ui --env=qa            # Run against QA environment
    """
    os.environ["TEST_ENV"] = env
    
    print("=" * 80)
    print("RUNNING UI TESTS")
    print(f"Environment: {env}")
    print("=" * 80)
    
    cmd = "python run_bdd_tests.py"
    
    if tags:
        cmd += f" --tags={tags}"
    
    if headless:
        # Set environment variable for headless mode
        os.environ["HEADLESS"] = "true"
    
    print(f"\nCommand: {cmd}\n")
    c.run(cmd, pty=False)
    
    print("\n" + "=" * 80)
    print("✅ UI TESTS COMPLETED")
    print("=" * 80)


@task
def test_all(c, env="staging"):
    """
    Run all tests (API + UI)
    Usage:
        invoke test-all                  # Run all tests (staging)
        invoke test-all --env=qa         # Run all tests against QA
    """
    os.environ["TEST_ENV"] = env
    
    print("=" * 80)
    print("RUNNING ALL TESTS")
    print(f"Environment: {env}")
    print("=" * 80)
    
    # Run API tests
    print("\n[1/2] Running API tests...")
    c.run("python -m pytest tests/api/ -v --tb=short", pty=False)
    
    # Run UI tests
    print("\n[2/2] Running UI tests...")
    c.run("python run_bdd_tests.py", pty=False)
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


@task
def test_regression(c, env="staging"):
    """
    Run regression test suite (API + UI)
    Usage:
        invoke test-regression               # Run regression (staging)
        invoke test-regression --env=qa      # Run regression against QA
    """
    os.environ["TEST_ENV"] = env
    
    print("=" * 80)
    print("RUNNING REGRESSION TESTS")
    print(f"Environment: {env}")
    print("=" * 80)
    
    # Run API regression tests
    print("\n[1/2] Running API regression tests...")
    c.run("python -m pytest tests/api/ -m regression -v --tb=short", pty=False)
    
    # Run UI regression tests
    print("\n[2/2] Running UI regression tests...")
    c.run("python run_bdd_tests.py --tags=@regression", pty=False)
    
    print("\n" + "=" * 80)
    print("✅ REGRESSION TESTS COMPLETED")
    print("=" * 80)


@task
def test_patient_login(c, create_account=False):
    """
    Run patient login tests
    Usage:
        invoke test-patient-login                    # Test with existing account
        invoke test-patient-login --create-account   # Test with new account creation
    """
    print("=" * 80)
    print("RUNNING PATIENT LOGIN TESTS")
    print("=" * 80)
    
    if create_account:
        cmd = "python -m pytest tests/api/test_patient_login.py::TestPatientLogin::test_patient_login_conditional[new_account] -v -s"
    else:
        cmd = "python -m pytest tests/api/test_patient_login.py -v -s"
    
    print(f"\nCommand: {cmd}\n")
    c.run(cmd, pty=False)
    
    print("\n" + "=" * 80)
    print("✅ PATIENT LOGIN TESTS COMPLETED")
    print("=" * 80)


# ============================================================================
# Allure Report Tasks
# ============================================================================

@task
def allure_generate(c):
    """
    Generate Allure report from results
    Usage: invoke allure-generate
    """
    print("=" * 80)
    print("GENERATING ALLURE REPORT")
    print("=" * 80)
    
    if not ALLURE_RESULTS_DIR.exists():
        print(f"❌ No results found at: {ALLURE_RESULTS_DIR}")
        print("Run tests first to generate results.")
        return
    
    # Remove old report
    if ALLURE_REPORT_DIR.exists():
        print(f"Removing old report: {ALLURE_REPORT_DIR}")
        shutil.rmtree(ALLURE_REPORT_DIR)
    
    # Generate new report
    cmd = f"allure generate {ALLURE_RESULTS_DIR} -o {ALLURE_REPORT_DIR} --clean"
    print(f"\nCommand: {cmd}\n")
    
    try:
        c.run(cmd, pty=False)
        print("\n" + "=" * 80)
        print(f"✅ REPORT GENERATED: {ALLURE_REPORT_DIR}")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Failed to generate report: {e}")
        print("Make sure Allure is installed: https://docs.qameta.io/allure/")


@task
def allure_open(c):
    """
    Open Allure report in browser
    Usage: invoke allure-open
    """
    print("=" * 80)
    print("OPENING ALLURE REPORT")
    print("=" * 80)
    
    if not ALLURE_REPORT_DIR.exists():
        print(f"❌ No report found at: {ALLURE_REPORT_DIR}")
        print("Generate report first: invoke allure-generate")
        return
    
    cmd = f"allure open {ALLURE_REPORT_DIR}"
    print(f"\nCommand: {cmd}\n")
    
    try:
        c.run(cmd, pty=False)
    except Exception as e:
        print(f"\n❌ Failed to open report: {e}")
        print("Make sure Allure is installed: https://docs.qameta.io/allure/")


@task
def allure_serve(c):
    """
    Generate and serve Allure report (opens in browser)
    Usage: invoke allure-serve
    """
    print("=" * 80)
    print("SERVING ALLURE REPORT")
    print("=" * 80)
    
    if not ALLURE_RESULTS_DIR.exists():
        print(f"❌ No results found at: {ALLURE_RESULTS_DIR}")
        print("Run tests first to generate results.")
        return
    
    cmd = f"allure serve {ALLURE_RESULTS_DIR}"
    print(f"\nCommand: {cmd}\n")
    
    try:
        c.run(cmd, pty=False)
    except Exception as e:
        print(f"\n❌ Failed to serve report: {e}")
        print("Make sure Allure is installed: https://docs.qameta.io/allure/")


@task
def allure_clear(c):
    """
    Clear Allure results and reports
    Usage: invoke allure-clear
    """
    print("=" * 80)
    print("CLEARING ALLURE DATA")
    print("=" * 80)
    
    cleared = []
    
    # Clear results
    if ALLURE_RESULTS_DIR.exists():
        shutil.rmtree(ALLURE_RESULTS_DIR)
        ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        cleared.append(f"Results: {ALLURE_RESULTS_DIR}")
    
    # Clear report
    if ALLURE_REPORT_DIR.exists():
        shutil.rmtree(ALLURE_REPORT_DIR)
        cleared.append(f"Report: {ALLURE_REPORT_DIR}")
    
    if cleared:
        print("\n✅ Cleared:")
        for item in cleared:
            print(f"  - {item}")
    else:
        print("\n✅ Nothing to clear")
    
    print("=" * 80)


@task
def allure_report(c):
    """
    Generate and open Allure report (convenience task)
    Usage: invoke allure-report
    """
    allure_generate(c)
    allure_open(c)


# ============================================================================
# Environment & Setup Tasks
# ============================================================================

@task
def clean(c):
    """
    Clean all generated files (reports, logs, cache)
    Usage: invoke clean
    """
    print("=" * 80)
    print("CLEANING PROJECT")
    print("=" * 80)
    
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        ".pytest_cache",
        "reports/logs/*",
        "reports/screenshots/*",
        "reports/videos/*",
    ]
    
    cleaned = []
    
    for pattern in patterns:
        for path in PROJECT_ROOT.glob(pattern):
            if path.is_file():
                path.unlink()
                cleaned.append(str(path.relative_to(PROJECT_ROOT)))
            elif path.is_dir():
                shutil.rmtree(path)
                cleaned.append(str(path.relative_to(PROJECT_ROOT)))
    
    if cleaned:
        print(f"\n✅ Cleaned {len(cleaned)} items")
    else:
        print("\n✅ Nothing to clean")
    
    print("=" * 80)


@task
def install(c):
    """
    Install project dependencies
    Usage: invoke install
    """
    print("=" * 80)
    print("INSTALLING DEPENDENCIES")
    print("=" * 80)
    
    c.run("pip install -r requirements.txt", pty=False)
    
    print("\n" + "=" * 80)
    print("✅ DEPENDENCIES INSTALLED")
    print("=" * 80)


@task
def setup(c):
    """
    Setup project (install dependencies + install Playwright browsers)
    Usage: invoke setup
    """
    print("=" * 80)
    print("SETTING UP PROJECT")
    print("=" * 80)
    
    # Install dependencies
    print("\n[1/2] Installing dependencies...")
    c.run("pip install -r requirements.txt", pty=False)
    
    # Install Playwright browsers
    print("\n[2/2] Installing Playwright browsers...")
    c.run("playwright install chromium", pty=False)
    
    print("\n" + "=" * 80)
    print("✅ PROJECT SETUP COMPLETED")
    print("=" * 80)


# ============================================================================
# Utility Tasks
# ============================================================================

@task
def lint(c):
    """
    Run code linting (flake8)
    Usage: invoke lint
    """
    print("=" * 80)
    print("RUNNING LINTER")
    print("=" * 80)
    
    try:
        c.run("flake8 business/ tests/ utilities/ --max-line-length=120 --exclude=__pycache__", pty=False)
        print("\n✅ LINTING PASSED")
    except:
        print("\n❌ LINTING FAILED")
    
    print("=" * 80)


@task
def format_code(c):
    """
    Format code with black
    Usage: invoke format-code
    """
    print("=" * 80)
    print("FORMATTING CODE")
    print("=" * 80)
    
    try:
        c.run("black business/ tests/ utilities/ --line-length=120", pty=False)
        print("\n✅ CODE FORMATTED")
    except:
        print("\n❌ Black not installed. Install with: pip install black")
    
    print("=" * 80)


@task
def info(c):
    """
    Display project information
    Usage: invoke info
    """
    print("=" * 80)
    print("PROJECT INFORMATION")
    print("=" * 80)
    
    print(f"\nProject Root: {PROJECT_ROOT}")
    print(f"Reports Dir:  {REPORTS_DIR}")
    print(f"Allure Results: {ALLURE_RESULTS_DIR}")
    print(f"Allure Report:  {ALLURE_REPORT_DIR}")
    
    # Count test files
    api_tests = len(list((PROJECT_ROOT / "tests" / "api").glob("test_*.py")))
    ui_features = len(list((PROJECT_ROOT / "tests" / "ui" / "features").glob("*.feature")))
    
    print(f"\nTest Files:")
    print(f"  - API Tests: {api_tests}")
    print(f"  - UI Features: {ui_features}")
    
    print("\n" + "=" * 80)


# ============================================================================
# Combined Workflow Tasks
# ============================================================================

@task
def test_and_report(c, test_type="all"):
    """
    Run tests and generate Allure report
    Usage:
        invoke test-and-report                  # Run all tests + report
        invoke test-and-report --test-type=api  # Run API tests + report
        invoke test-and-report --test-type=ui   # Run UI tests + report
        invoke test-and-report --test-type=smoke # Run smoke tests + report
    """
    print("=" * 80)
    print(f"RUNNING {test_type.upper()} TESTS + GENERATING REPORT")
    print("=" * 80)
    
    # Clear old results
    allure_clear(c)
    
    # Run tests based on type
    if test_type == "api":
        test_api(c)
    elif test_type == "ui":
        test_ui(c)
    elif test_type == "smoke":
        test_smoke(c)
    else:
        test_all(c)
    
    # Generate and open report
    allure_report(c)


@task
def ci(c):
    """
    Run CI pipeline (clean, test all, generate report)
    Usage: invoke ci
    """
    print("=" * 80)
    print("RUNNING CI PIPELINE")
    print("=" * 80)
    
    # Clean
    print("\n[1/4] Cleaning...")
    clean(c)
    
    # Clear Allure
    print("\n[2/4] Clearing old reports...")
    allure_clear(c)
    
    # Run all tests
    print("\n[3/4] Running all tests...")
    test_all(c)
    
    # Generate report
    print("\n[4/4] Generating report...")
    allure_generate(c)
    
    print("\n" + "=" * 80)
    print("✅ CI PIPELINE COMPLETED")
    print("=" * 80)
