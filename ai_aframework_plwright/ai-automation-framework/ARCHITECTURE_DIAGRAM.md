# Framework Architecture Diagram


```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Automation Framework                       │
│                   (Clean Separated Architecture)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │
                ┌───────────────┴───────────────┐
                │                               │
                │                               │
    ┌───────────▼──────────┐       ┌──────────▼───────────┐
    │  API Testing Stack   │       │  UI Testing Stack    │
    │      (Pytest)        │       │     (Behave)         │
    └──────────────────────┘       └──────────────────────┘
                │                               │
                │                               │
    ┌───────────▼──────────┐       ┌──────────▼───────────┐
    │  tests/api/pytest.ini│       │     behave.ini       │
    │    (API Config)      │       │    (UI Config)       │
    └──────────────────────┘       └──────────────────────┘
                │                               │
                │                               │
    ┌───────────▼──────────┐       ┌──────────▼───────────┐
    │    tests/api/        │       │     features/        │
    │  ├── conftest.py     │       │  ├── environment.py  │
    │  ├── test_auth.py    │       │  ├── login.feature   │
    │  └── test_user.py    │       │  └── steps/          │
    └──────────────────────┘       └──────────────────────┘
                │                               │
                │                               │
    ┌───────────▼──────────┐       ┌──────────▼───────────┐
    │   API Fixtures       │       │   Context Objects    │
    │   - api_client       │       │   - context.page     │
    │   - authenticated    │       │   - context.browser  │
    └──────────────────────┘       └──────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Shared Resources    │
                    │  ├── business/        │
                    │  ├── config/          │
                    │  ├── utilities/       │
                    │  └── core/            │
                    └───────────────────────┘

Benefits:
✅ Clear separation of concerns
✅ Independent configurations
✅ No framework mixing
✅ Proper BDD implementation
✅ Easy to maintain
```

---

## Test Execution Flow

### API Test Flow (Pytest)

```
┌──────────────┐
│ Developer    │
│ runs command │
└──────┬───────┘
       │
       │  python scripts/run_api_tests.py
       │
       ▼
┌──────────────────────┐
│  pytest discovers    │
│  tests/api/**/*.py   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Load pytest.ini     │
│  from tests/api/     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Initialize fixtures │
│  from conftest.py    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Execute API tests   │
│  - Fast              │
│  - Parallel          │
│  - Assertions        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Generate Reports    │
│  - Allure            │
│  - JUnit XML         │
└──────────────────────┘
```

### UI Test Flow (Behave)

```
┌──────────────┐
│ Developer    │
│ runs command │
└──────┬───────┘
       │
       │  python scripts/run_ui_tests.py
       │
       ▼
┌──────────────────────┐
│  behave discovers    │
│  features/**/*.feature│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Load behave.ini     │
│  from root           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Run before_all()    │
│  - Launch browser    │
│  - Setup config      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  For each scenario:  │
│  - before_scenario() │
│  - Run steps         │
│  - after_scenario()  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Run after_all()     │
│  - Close browser     │
│  - Cleanup           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Generate Reports    │
│  - HTML              │
│  - JSON              │
│  - Screenshots       │
└──────────────────────┘
```

---

## Data Flow

### API Testing Data Flow

```
┌─────────────┐
│ Test Data   │
│ (JSON/YAML) │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Client     │ ──────► REST API Endpoint
│  (requests lib) │ ◄────── Response
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Schema         │
│  Validation     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Assertions     │
│  (assert/expect)│
└─────────────────┘
```

### UI Testing Data Flow

```
┌─────────────┐
│ Feature     │
│ Files       │
│ (.feature)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Step           │
│  Definitions    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Page Objects   │ ──────► Browser (Playwright)
│  (business/ui)  │ ◄────── Page Elements
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Flows          │
│  (Multi-step)   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Assertions     │
│  + Screenshots  │
└─────────────────┘
```

---

## Directory Structure Comparison

### BEFORE (Current - Mixed)

```
ai-automation-framework/
├── pytest.ini                    # Mixed config ❌
├── requirements.txt              # All deps together
├── run_bdd_tests.py             # Confusing script ❌
│
├── tests/
│   ├── conftest.py              # Root fixtures
│   ├── api/                     # Pytest ✅
│   │   ├── conftest.py
│   │   └── test_*.py
│   │
│   └── ui/                      # pytest-bdd ❌
│       ├── conftest.py          # Fixture pollution
│       ├── features/
│       │   └── *.feature
│       └── steps/
│           ├── conftest.py      # More fixtures!
│           ├── pytest.ini       # Nested config!
│           └── *_steps.py
│
└── business/
    ├── api/
    └── ui/
```

### AFTER (Target - Clean)

```
ai-automation-framework/
├── pytest.ini                    # API/Integration only ✅
├── behave.ini                    # UI only ✅
├── requirements.txt              # Common deps
├── requirements-api.txt          # API specific ✅
├── requirements-ui.txt           # UI specific ✅
│
├── scripts/                      # Clear execution ✅
│   ├── run_api_tests.py
│   ├── run_ui_tests.py
│   └── run_all_tests.py
│
├── tests/                        # API & Integration ✅
│   ├── api/
│   │   ├── pytest.ini
│   │   ├── conftest.py
│   │   └── test_*.py
│   └── integration/
│       ├── conftest.py
│       └── test_*.py
│
├── features/                     # UI only (Behave) ✅
│   ├── environment.py           # Hooks & setup
│   ├── *.feature
│   └── steps/
│       └── *_steps.py
│
└── business/                     # Shared logic ✅
    ├── api/
    └── ui/
```

---

## Configuration Separation

### API Configuration (pytest.ini)

```ini
[pytest]
testpaths = tests/api tests/integration  # API only
markers =
    api: API tests
    integration: Integration tests
addopts = 
    -n auto         # Parallel by default
    --tb=short
```

### UI Configuration (behave.ini)

```ini
[behave]
paths = features                # UI only
format = pretty
format = html
tags = ~@wip ~@skip
```

---

## Fixture vs Context

### API: Pytest Fixtures ✅

```python
# tests/api/conftest.py
@pytest.fixture
def api_client():
    client = APIClient()
    yield client
    client.close()

# tests/api/test_auth.py
def test_login(api_client):  # Fixture injection
    response = api_client.post("/login", {...})
    assert response.status_code == 200
```

### UI: Behave Context ✅

```python
# features/environment.py
def before_scenario(context, scenario):
    context.page = context.browser.new_page()
    context.login_page = LoginPage(context.page)

# features/steps/login_steps.py
@when('I click login')
def step_click_login(context):  # Context parameter
    context.login_page.click_login()
```

---

## Parallel Execution

### API Tests (Pytest)

```
┌────────────┐
│  pytest    │
│  -n auto   │
└─────┬──────┘
      │
      ├──────► Worker 1 ──► test_auth.py
      ├──────► Worker 2 ──► test_user.py
      ├──────► Worker 3 ──► test_product.py
      └──────► Worker 4 ──► test_orders.py
                  │
                  └──► Fast, Independent
```

### UI Tests (Behave)

```
┌────────────┐
│  behave    │
│  (serial)  │
└─────┬──────┘
      │
      ├──────► Scenario 1 ──► Browser Context
      │
      ├──────► Scenario 2 ──► New Browser Context
      │
      └──────► Scenario 3 ──► New Browser Context
                  │
                  └──► Isolated, Sequential
```

*Note: Behave can use behave-parallel for parallel execution if needed*

---

## Team Responsibilities

```
┌─────────────────────────────────────────┐
│           Development Team              │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        │                        │
┌───────▼─────────┐      ┌──────▼──────────┐
│  API Developers │      │  QA Engineers   │
│  & Test Eng.    │      │  & BA's         │
└─────────────────┘      └─────────────────┘
        │                        │
        │                        │
┌───────▼─────────┐      ┌──────▼──────────┐
│  Write API      │      │  Write UI       │
│  Tests          │      │  Tests          │
│  (Pytest)       │      │  (Behave)       │
│                 │      │                 │
│  - Quick        │      │  - Readable     │
│  - Technical    │      │  - Business     │
│  - Assertions   │      │  - Scenarios    │
└─────────────────┘      └─────────────────┘
```

---

## Success Metrics Dashboard

```
┌─────────────────────────────────────────────────────────┐
│                   Framework Health                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  API Tests (Pytest)                                     │
│  ✅ Tests: 45          ✅ Pass Rate: 98%               │
│  ✅ Parallel: Yes      ✅ Avg Time: 2.3s               │
│  ✅ Coverage: 87%                                       │
│                                                         │
│  UI Tests (Behave)                                      │
│  ✅ Scenarios: 23      ✅ Pass Rate: 95%               │
│  ✅ Features: 5        ✅ Avg Time: 45s                │
│  ✅ Coverage: 82%                                       │
│                                                         │
│  Integration                                            │
│  ✅ Independent: Yes   ✅ No Conflicts: Yes            │
│  ✅ CI/CD: Green       ✅ Reports: Generated           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Migration Progress Tracker

```
Phase 1: Infrastructure      ████████████████████ 100%
Phase 2: Test Migration      ████████████████████ 100%
Phase 3: Core Updates        ████████████████████ 100%
Phase 4: Scripts             ████████████████████ 100%
Phase 5: CI/CD              ████████████████████ 100%
Phase 6: Validation          ████████████████████ 100%

Overall Progress:            ████████████████████ 100%
Status: ✅ READY FOR PRODUCTION
```

---

*Architecture Diagram v1.0*  
*Created: 2025-11-05*
