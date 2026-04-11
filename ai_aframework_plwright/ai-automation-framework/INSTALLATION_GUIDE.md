# AI-Driven Automation Framework - Installation Guide

## What's Included

This framework provides production-ready automation testing with:

- UI Testing (Playwright + Behave BDD)
- API Testing (Requests + Pytest)
- AI Self-Healing Mechanism (DOM analysis, text/attribute/AI-based strategies)
- Allure Reporting
- Multi-Environment Configuration (qa, staging, production, local, demo)
- CI/CD Integration (Jenkins & GitHub Actions)

## Prerequisites

- Python 3.11 or higher
- pip

## Quick Start

### 1. Install Dependencies

`ash
pip install -r requirements.txt
`

### 2. Install Playwright Browsers

`ash
playwright install chromium
`

### 3. Configure Environment

Edit `config/environments.yaml` with your target URLs, credentials, and feature flags.

### 4. Run Tests

`ash
# Run smoke tests against QA
python -m invoke test-smoke --env=qa

# Run API tests
python -m invoke test-api

# Run UI tests
python run_bdd_tests.py --env=staging --tags=@smoke

# Run full regression
python -m invoke test-regression --env=staging
`

### 5. View Reports

`ash
# Generate and serve Allure report
allure serve reports/allure-results

# Or generate and open
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
`

## Project Structure

`
ai-automation-framework/
+-- config/              # Configuration management
|   +-- config.py        # Singleton config loader
|   +-- environments.yaml
|   +-- test_suites.yaml
+-- core/                # Core framework components
|   +-- driver_factory.py
|   +-- api_client.py
|   +-- base_test.py
+-- business/            # Business logic layer
|   +-- ui/              # Page objects & flows
|   +-- api/             # API endpoints
+-- ai/                  # AI components
|   +-- self_healing/    # Self-healing engine & agents
|   +-- failure_analysis/
|   +-- test_generation/
+-- utilities/           # Logger, helpers, data generator, etc.
+-- tests/
|   +-- api/             # API tests (pytest)
|   +-- ui/              # UI tests (behave BDD)
+-- ci_cd/               # CI/CD configs
+-- tasks.py             # Invoke task runner
+-- run_bdd_tests.py     # UI test runner
+-- run_api_tests.py     # API test runner
+-- run_all_tests.py     # Combined runner
`

## Running Different Test Types

`ash
# API tests (pytest)
python -m pytest tests/api/ -v
python -m pytest tests/api/ -m smoke -v

# UI tests (behave) -- --env is required
python run_bdd_tests.py --env=qa
python run_bdd_tests.py --env=staging --tags=@smoke

# All tests
python run_all_tests.py --env=staging

# Using invoke tasks
python -m invoke test-api
python -m invoke test-ui --env=qa --tags=@smoke
python -m invoke test-demo --env=demo
python -m invoke test-all --env=staging
`

## Configuration

### Environment Configuration

Edit `config/environments.yaml` to add or modify environments:

`yaml
qa:
  base_url: "https://qa.example.com"
  api_base_url: "https://api-qa.example.com"
  browser: chromium
  headless: true
  timeout: 30000
  credentials:
    standard:
      username: "user@test.com"
      password: "password"
  features:
    self_healing: true
    ai_analysis: true
`

## AI Self-Healing

The framework automatically heals broken locators using three strategies:

1. **Text-based healing** - Finds elements by visible text content
2. **Attribute-based healing** - Uses stable HTML attributes (data-testid, aria-label, name, etc.)
3. **AI-based healing** - DOM analysis with weighted feature scoring (tag, text, attributes, classes, position)

Healing events are logged, stored in SQLite, and reported in Allure.

## Writing Tests

### UI Test (Behave BDD)

`gherkin
# tests/ui/features/login.feature
Feature: Login
  Scenario: User logs in successfully
    Given I am using the "staging" environment
    When I open the CareLink page
    Then I should see the login form
    When I login as "standard" user
    Then I should be logged in successfully
`

### API Test (Pytest)

`python
import pytest

@pytest.mark.api
@pytest.mark.smoke
def test_get_user(authenticated_api_client):
    response = authenticated_api_client.get("/users/1")
    assert response.status_code == 200
`

## Troubleshooting

**Playwright browsers not installed:**
`ash
playwright install --with-deps
`

**Module not found:**
`ash
pip install -r requirements.txt
`

**Tests failing with timeout:**
Increase timeout in `config/environments.yaml`.

**--env required error for UI tests:**
Always pass `--env=<environment>` when running `run_bdd_tests.py`.
