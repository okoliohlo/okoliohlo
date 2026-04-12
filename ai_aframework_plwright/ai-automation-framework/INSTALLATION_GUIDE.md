# AI-Driven Automation Framework - Installation Guide

## What's Included

- **UI Testing** — Playwright + Behave BDD
- **API Testing** — Requests + Pytest
- **AI Self-Healing** — DOM analysis with text / attribute / AI-based strategies
- **Allure Reporting** — Screenshots, videos, step logs
- **Multi-Environment Config** — qa, staging, production, local, demo
- **CI/CD Integration** — Jenkins & GitHub Actions

## Prerequisites

- Python 3.11+
- pip
- Allure CLI (for reports) — [install guide](https://docs.qameta.io/allure/#_installing_a_commandline)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Configure Environment

Edit `config/environments.yaml` with your target URLs, credentials, and feature flags.

```yaml
demo:
  base_url: "https://profile.okoliohlo.com/"
  browser: "chromium"
  headless: false
  timeout: 30000
  viewport_width: 1920
  viewport_height: 1080
  credentials:
    standard:
      username: "user@test.com"
      password: "password"
  features:
    self_healing: true
    ai_analysis: true
```

### 4. Run Tests

```bash
# UI tests (Behave BDD) — --env is required
python run_bdd_tests.py --env=demo
python run_bdd_tests.py --env=demo --tags=@smoke
python run_bdd_tests.py --env=demo --tags=@demo --clean   # clean Allure results first

# API tests (Pytest)
python -m pytest tests/api/ -v
python -m pytest tests/api/ -m smoke -v

# All tests
python run_all_tests.py --env=staging

# Using invoke tasks
python -m invoke test-api
python -m invoke test-ui --env=qa --tags=@smoke
python -m invoke test-demo --env=demo
python -m invoke test-all --env=staging
```

### 5. View Reports

```bash
# Generate and serve Allure report
allure serve reports/allure-results

# Or generate and open
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## Project Structure

```
ai-automation-framework/
├── config/                # Configuration management
│   ├── config.py          # Singleton config loader
│   ├── environments.yaml  # Per-environment settings
│   └── test_suites.yaml   # Test suite definitions
├── core/                  # Core framework components
│   ├── driver_factory.py  # Playwright browser management (singleton)
│   ├── api_client.py      # HTTP client wrapper
│   └── base_test.py       # BaseTest / UITest / APITest / IntegrationTest
├── business/              # Business logic layer
│   ├── ui/                # Page objects & user flows
│   │   ├── pages/         # Page Object Model classes
│   │   └── flows/         # Multi-page workflow helpers
│   └── api/               # API endpoints & schemas
│       ├── endpoints/
│       └── schemas/
├── ai/                    # AI components
│   ├── self_healing/      # Self-healing engine & agents
│   └── failure_analysis/  # Failure categoriser
├── utilities/             # Logger, helpers, data generator, screenshots
├── tests/
│   ├── ui/                # UI tests (Behave BDD)
│   │   ├── features/      # .feature files
│   │   ├── steps/         # Step definitions
│   │   └── environment.py # Behave hooks (uses UITest)
│   ├── api/               # API tests (Pytest)
│   └── integration/       # E2E tests (Pytest, inherits IntegrationTest)
├── ci_cd/                 # Jenkins, GitHub Actions, Docker
├── scripts/               # Utility scripts (setup, cleanup, helpers)
├── run_bdd_tests.py       # UI test runner (Behave)
├── run_api_tests.py       # API test runner (Pytest)
├── run_all_tests.py       # Combined runner
└── tasks.py               # Invoke task definitions
```

## Architecture: How Tests Are Executed

### UI Tests (Behave)

```
run_bdd_tests.py
  └─ behave
       └─ environment.py hooks
            ├─ before_all()      → session config, AllureStepHelper
            ├─ before_scenario() → UITest()._setup() → DriverFactory → browser context + page
            ├─ steps execute     → use context.page (Playwright Page)
            └─ after_scenario()  → UITest._teardown() → screenshot/video, close context
```

### API / Integration Tests (Pytest)

```
pytest tests/api/
  └─ conftest.py fixtures provide api_client, auth_endpoint, etc.

pytest tests/integration/
  └─ test classes inherit IntegrationTest (UITest + APITest)
       └─ BaseTest.setup_teardown autouse fixture → _setup() / _teardown()
```

## AI Self-Healing

The framework automatically heals broken locators using three strategies:

1. **Text-based** — Finds elements by visible text content
2. **Attribute-based** — Uses stable HTML attributes (data-testid, aria-label, name, etc.)
3. **AI-based** — DOM analysis with weighted feature scoring (tag, text, attributes, classes, position)

Healing events are logged, stored in SQLite, and reported in Allure.

Enable/disable in `config/environments.yaml`:

```yaml
features:
  self_healing: true
  ai_analysis: true
```

## Writing Tests

### UI Test (Behave BDD)

```gherkin
# tests/ui/features/my_feature.feature
Feature: Contact page validation
  @smoke @ui
  Scenario: User navigates to contact form
    When I open the Profile page
    Then I should see the Okoliohlo profile homepage
    When I click the Contact button
    Then I should see the Contact form
```

### API Test (Pytest)

```python
import pytest

@pytest.mark.api
@pytest.mark.smoke
def test_login_api(auth_endpoint):
    credentials = config.get_credentials("standard")
    response = auth_endpoint.login(credentials["username"], credentials["password"])
    assert "token" in response
```

## Troubleshooting

**Playwright browsers not installed:**
```bash
playwright install --with-deps
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Tests failing with timeout:**
Increase `timeout` in `config/environments.yaml`.

**`--env` required error for UI tests:**
Always pass `--env=<environment>` when running `run_bdd_tests.py`.

## Additional Resources

- [Playwright Python docs](https://playwright.dev/python/)
- [Pytest docs](https://docs.pytest.org/)
- [Behave docs](https://behave.readthedocs.io/)
- [Allure docs](https://docs.qameta.io/allure/)
