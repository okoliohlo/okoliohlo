# Framework Architecture Diagram


`
+------------------------------------------------------------------+
|                    AI Automation Framework                        |
|                (Playwright + Behave + Pytest)                     |
+------------------------------------------------------------------+
                                |
                +---------------+----------------+
                |                                |
    +-----------v-----------+       +------------v-----------+
    |  API Testing Stack    |       |  UI Testing Stack      |
    |      (Pytest)         |       |     (Behave BDD)       |
    +----------+------------+       +------------+-----------+
               |                                 |
    +----------v------------+       +------------v-----------+
    |  pytest.ini (root)    |       |     behave.ini         |
    +----------+------------+       +------------+-----------+
               |                                 |
    +----------v------------+       +------------v-----------+
    |    tests/api/         |       |  tests/ui/features/    |
    |  +-- conftest.py      |       |  +-- environment.py    |
    |  +-- test_*.py        |       |  +-- *.feature         |
    +----------+------------+       |  +-- steps/            |
               |                    +------------+-----------+
               |                                 |
    +----------v------------+       +------------v-----------+
    |   Pytest Fixtures     |       |   Behave Context       |
    |   - api_client        |       |   - context.page       |
    |   - auth_endpoint     |       |   - context.browser    |
    +----------+------------+       +------------+-----------+
               |                                 |
               +----------------+----------------+
                                |
                    +-----------v-----------+
                    |   Shared Resources    |
                    |  +-- business/        |
                    |  +-- config/          |
                    |  +-- utilities/       |
                    |  +-- core/            |
                    |  +-- ai/             |
                    +-----------------------+
`

---

## Test Execution Flow

### API Test Flow (Pytest)

`
Developer runs: python run_api_tests.py
        |
        v
pytest discovers tests/api/**/*.py
        |
        v
Load pytest.ini from project root
        |
        v
Initialize fixtures from conftest.py
        |
        v
Execute API tests (fast, parallel, assertions)
        |
        v
Generate Allure reports
`

### UI Test Flow (Behave)

`
Developer runs: python run_bdd_tests.py --env=staging
        |
        v
behave discovers tests/ui/features/**/*.feature
        |
        v
Load behave.ini from project root
        |
        v
Run before_all() -- Launch browser via DriverFactory
        |
        v
For each scenario:
  before_scenario() -> Run steps -> after_scenario()
        |
        v
Run after_all() -- Close browser, cleanup
        |
        v
Generate Allure reports + screenshots
`

---

## AI Self-Healing Architecture

`
Element interaction fails
        |
        v
+-------------------+
| HealingEngine     |  Entry point (called from DriverFactory)
+--------+----------+
         |
         v
+-------------------+
| HealingCoordinator|  Orchestrates multi-agent pipeline
+--------+----------+
         |
    +----+----+----+
    |         |    |
    v         v    v
Classifier  Reasoner  Executor
(failure    (repair   (run strategies
 type)      proposals) on live page)
    |         |    |
    +----+----+----+
         |
         v
+-------------------+
| Strategies        |
| 1. Text-Based     |  Priority 10
| 2. Attribute-Based|  Priority 20
| 3. AI/DOM-Based   |  Priority 30
+-------------------+
         |
         v
+-------------------+
| ElementValidator  |  Confidence scoring
+-------------------+
         |
         v
+-------------------+
| HealingDatabase   |  SQLite memory + audit log
+-------------------+
         |
         v
+-------------------+
| SourceUpdater     |  Auto/prompt/pending code update
+-------------------+
`

---

## Directory Structure

`
ai-automation-framework/
+-- config/                  # Configuration
|   +-- config.py            # Singleton config loader
|   +-- environments.yaml    # Per-environment settings
|   +-- test_suites.yaml     # Test suite definitions
+-- core/                    # Framework core
|   +-- driver_factory.py    # Playwright browser management
|   +-- api_client.py        # HTTP client with retry/logging
|   +-- base_test.py         # Base test classes
+-- business/                # Business logic
|   +-- api/endpoints/       # API endpoint wrappers
|   +-- ui/pages/            # Page objects (BasePage + pages)
|   +-- ui/flows/            # Multi-step workflows
+-- ai/                      # AI components
|   +-- self_healing/        # Healing engine, agents, strategies, DB
|   +-- failure_analysis/    # Failure analyzer
|   +-- test_generation/     # Test generator from page objects
+-- utilities/               # Shared helpers
|   +-- logger.py            # Centralized logging
|   +-- helpers.py           # Retry, wait, random data, etc.
|   +-- data_generator.py    # Faker-based test data
|   +-- file_handler.py      # JSON/YAML/CSV I/O
|   +-- screenshot_manager.py# Capture & compare screenshots
|   +-- mailinator_helper.py # Email/MFA verification
+-- tests/
|   +-- api/                 # Pytest API tests + conftest
|   +-- ui/features/         # Behave features + steps
+-- test_management/         # Coverage analyzer, test tracker
+-- ci_cd/                   # Jenkins, GitHub Actions, Docker
+-- tasks.py                 # Invoke task runner
+-- run_bdd_tests.py         # UI test runner (--env required)
+-- run_api_tests.py         # API test runner
+-- run_all_tests.py         # Combined runner
+-- pytest.ini               # Pytest config (API tests)
+-- behave.ini               # Behave config (UI tests)
+-- requirements.txt         # Python dependencies
`

---

## Configuration Separation

### API Configuration (pytest.ini)

`ini
[pytest]
testpaths = tests/api tests/integration
markers =
    smoke: Smoke tests
    regression: Regression tests
    api: API tests
`

### UI Configuration (behave.ini)

`ini
[behave]
paths = tests/ui/features
default_tags = -wip,-skip
`

---

*Architecture Diagram v2.0*
