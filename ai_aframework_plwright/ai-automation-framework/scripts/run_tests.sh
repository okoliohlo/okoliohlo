#!/bin/bash

# Test execution script

# Default values
ENV=${TEST_ENV:-qa}
BROWSER=${BROWSER:-chromium}
WORKERS=${PARALLEL_WORKERS:-4}
SUITE=${TEST_SUITE:-smoke}
HEADLESS=${HEADLESS:-true}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENV="$2"
            shift 2
            ;;
        --browser)
            BROWSER="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --suite)
            SUITE="$2"
            shift 2
            ;;
        --headless)
            HEADLESS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "Running Tests"
echo "========================================="
echo "Environment: $ENV"
echo "Browser: $BROWSER"
echo "Suite: $SUITE"
echo "Workers: $WORKERS"
echo "Headless: $HEADLESS"
echo "========================================="

# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/ \
    --env="$ENV" \
    --browser="$BROWSER" \
    --headless="$HEADLESS" \
    -n "$WORKERS" \
    -m "$SUITE" \
    --alluredir=reports/allure-results \
    --html=reports/report.html \
    --self-contained-html \
    -v

# Store exit code
TEST_EXIT_CODE=$?

# Generate Allure report
echo ""
echo "========================================="
echo "Generating Allure Report"
echo "========================================="
allure generate reports/allure-results -o reports/allure-report --clean

echo ""
echo "========================================="
echo "Test Execution Complete"
echo "========================================="
echo "Exit code: $TEST_EXIT_CODE"
echo "HTML Report: reports/report.html"
echo "Allure Report: reports/allure-report/index.html"
echo ""
echo "To view Allure report, run:"
echo "  allure open reports/allure-report"
echo ""

exit $TEST_EXIT_CODE