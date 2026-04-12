# Framework Architecture Diagram


```
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
    |    pytest.ini (root)  |       |     behave.ini         |
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
    |   - api_client        |       |   - context.ui_test    |
    |   - auth_endpoint     |       |   - context.page       |
    +----------+------------+       |   - context.browser_ctx|
               |                    +------------+-----------+
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
```

---

## Test Execution Flow

### API Test Flow (Pytest)

```
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
  - api_client, auth_endpoint, user_endpoint
        |
        v
Execute API tests (fast, parallel, assertions)
        |
        v
Generate Allure reports
```

### UI Test Flow (Behave)

```
Developer runs: python run_bdd_tests.py --env=demo --tags=@smoke
        |
        v
behave discovers tests/ui/features/**/*.feature
        |
        v
Load behave.ini from project root
        |
        v
Run before_all()
  - Init AllureStepHelper
  - Log session config
        |
        v
For each scenario:
  before_scenario()
    - UITest()._setup()
    - DriverFactory.create_context() -> browser context
    - DriverFactory.create_page()   -> page + self-healing
    - Expose context.page, context.ui_test
        |
        v
  Run scenario steps (use context.page)
        |
        v
  after_scenario()
    - UITest._teardown(failed=..., test_name=...)
    - Screenshot on failure, video capture
    - Close browser context
        |
        v
Run after_all()
  - DriverFactory.cleanup()
        |
        v
Generate Allure reports + screenshots + videos
```

### Integration Test Flow (Pytest)

```
Developer runs: pytest tests/integration/
        |
        v
Test class inherits IntegrationTest (UITest + APITest)
        |
        v
BaseTest.setup_teardown autouse fixture fires:
  _setup() -> DriverFactory (browser) + APIClient
        |
        v
Execute test methods (UI + API combined)
        |
        v
_teardown() -> screenshot on failure, close context
```

---

## Core Architecture: BaseTest Hierarchy

```
BaseTest (core/base_test.py)
  |-- setup_teardown   @pytest.fixture(autouse=True)
  |-- _setup()         override in subclasses
  |-- _teardown()      supports pytest request OR behave scenario
  |-- capture_screenshot()
  |
  +-- UITest(BaseTest)
  |     _setup() -> DriverFactory.create_context() + create_page()
  |     Used by: Behave environment.py, Integration tests
  |
  +-- APITest(BaseTest)
  |     _setup() -> APIClient()
  |
  +-- IntegrationTest(UITest, APITest)
        _setup() -> UITest._setup() + APIClient()
```

---

## AI Self-Healing Architecture

```
Element interaction fails (DriverFactory._self_healing_locator)
        |
        v
+-------------------+
| HealingEngine     |  Entry point (facade for DriverFactory)
| healing_engine.py |  - record_success(): store element metadata
|                   |  - heal(): delegate to coordinator
+--------+----------+
         |
         v
+-------------------+
| HealingCoordinator|  Orchestrates multi-agent pipeline
| agents/           |  1. Memory recall (skip if cached heal works)
| coordinator.py    |  2. Classify -> Propose -> Execute -> Record
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
| Strategies        |  ai/self_healing/strategies/
| 1. Text-Based     |  Priority 10 — find by visible text
| 2. Attribute-Based|  Priority 20 — find by stable attrs
| 3. AI/DOM-Based   |  Priority 30 — weighted DOM analysis
+-------------------+
         |
         v
+-------------------+
| ElementValidator  |  Confidence scoring (tag, text, attrs, visibility)
| element_validator |  Threshold-based pass/fail
+-------------------+
         |
         v
+-------------------+
| HealingDatabase   |  SQLite (WAL mode, thread-safe singleton)
| database.py       |  Tables: element_metadata, selector_history,
|                   |          healing_memory, audit_log
+-------------------+
         |
         v
+-------------------+
| SourceUpdater     |  Auto/prompt/pending code update
| source_updater.py |  Guards: feature flag, confidence threshold,
|                   |          single-occurrence check
+-------------------+

Supporting modules:
  schemas.py            — shared dataclasses & enums
  locator_repository.py — backward-compat wrapper over HealingDatabase
```

---

## Directory Structure

```
ai-automation-framework/
+-- config/                  # Configuration
|   +-- config.py            # Singleton config loader
|   +-- environments.yaml    # Per-environment settings
|   +-- test_suites.yaml     # Test suite definitions
+-- core/                    # Framework core
|   +-- driver_factory.py    # Playwright browser management (singleton)
|   +-- api_client.py        # HTTP client with retry/logging
|   +-- base_test.py         # BaseTest / UITest / APITest / IntegrationTest
+-- business/                # Business logic
|   +-- api/endpoints/       # API endpoint wrappers
|   +-- ui/pages/            # Page objects (BasePage + pages)
|   +-- ui/flows/            # Multi-step workflows
+-- ai/                      # AI components
|   +-- self_healing/        # Healing engine, agents, strategies, DB
|   |   +-- agents/          # classifier, reasoner, executor, coordinator
|   |   +-- strategies/      # text_based, attribute_based, ai_based
|   |   +-- data/            # self_healing.db (SQLite)
|   |   +-- healing_engine.py
|   |   +-- database.py
|   |   +-- element_validator.py
|   |   +-- source_updater.py
|   |   +-- schemas.py
|   |   +-- locator_repository.py
|   +-- failure_analysis/    # FailureAnalyzer (pattern-based categoriser)
|   +-- test_generation/     # AITestGenerator (AST-based test scaffolding)
+-- utilities/               # Shared helpers
|   +-- logger.py            # Centralized logging
|   +-- helpers.py           # Retry, wait, random data, etc.
|   +-- data_generator.py    # Faker-based test data
|   +-- file_handler.py      # JSON/YAML/CSV I/O
|   +-- screenshot_manager.py# Capture & compare screenshots
|   +-- allure_helper.py     # Allure step logging & screenshot attach
|   +-- mailinator_helper.py # Email/MFA verification
+-- tests/
|   +-- api/                 # Pytest API tests + conftest
|   +-- ui/                  # Behave UI tests
|   |   +-- features/        # .feature files
|   |   +-- steps/           # Step definitions
|   |   +-- environment.py   # Behave hooks (uses UITest)
|   +-- integration/         # Pytest integration tests (IntegrationTest)
+-- test_management/         # Coverage analyzer, test tracker
+-- ci_cd/                   # Jenkins, GitHub Actions, Docker
+-- scripts/                 # Setup, cleanup, helper scripts
+-- tasks.py                 # Invoke task runner
+-- run_bdd_tests.py         # UI test runner (--env required)
+-- run_api_tests.py         # API test runner
+-- run_all_tests.py         # Combined runner
+-- pytest.ini               # Pytest config (API tests)
+-- behave.ini               # Behave config (UI tests)
+-- requirements.txt         # Python dependencies
```

---

## Configuration Separation

### API Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests/api tests/integration
markers =
    smoke: Smoke tests
    regression: Regression tests
    api: API tests
```

### UI Configuration (behave.ini)

```ini
[behave]
paths = tests/ui/features
default_tags = -wip,-skip
```

---

*Architecture Diagram v3.0*
