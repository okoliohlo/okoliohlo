# AI-Driven Automation Framework - Installation Guide

## 📦 What's Included

This archive contains a complete, production-ready automation testing framework with:

- ✅ UI Testing (Playwright)
- ✅ API Testing (Requests)  
- ✅ AI Self-Healing Mechanism
- ✅ Parallel Execution
- ✅ Allure Reporting
- ✅ CI/CD Integration (Jenkins & GitHub Actions)
- ✅ Docker Support
- ✅ Multi-Environment Configuration

## 🚀 Quick Start

### 1. Extract Archive

```bash
tar -xzf ai-automation-framework.tar.gz
cd ai-automation-framework
```

### 2. Run Setup

```bash
chmod +x scripts/*.sh
./scripts/setup.sh
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Tests

```bash
# Run smoke tests
./scripts/run_tests.sh --suite smoke

# Run full regression
./scripts/run_tests.sh --suite regression --workers 4
```

### 5. View Reports

```bash
# Open Allure report
allure serve reports/allure-results

# Or open HTML report
open reports/report.html
```

## 📋 Prerequisites

- Python 3.11 or higher
- pip
- Git (optional)

## 🛠️ Manual Setup (if script fails)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install --with-deps

# Run tests
pytest tests/ -m smoke -v
```

## 📁 Project Structure

```
ai-automation-framework/
├── config/              # Configuration management
├── core/                # Core framework components
├── business/            # Business logic layer
│   ├── ui/             # UI pages and flows
│   └── api/            # API endpoints
├── ai/                  # AI components
│   ├── self_healing/   # Self-healing engine
│   └── failure_analysis/ # Failure analyzer
├── utilities/           # Utility functions
├── tests/               # Test cases
│   ├── ui/             # UI tests
│   ├── api/            # API tests
│   └── integration/    # E2E tests
├── ci_cd/               # CI/CD configs
└── scripts/             # Utility scripts
```

## 🎯 Running Different Test Types

```bash
# UI tests only
pytest -m ui -v

# API tests only  
pytest -m api -v

# Smoke tests
pytest -m smoke -v

# Regression suite
pytest -m regression -v

# Specific test file
pytest tests/ui/test_login.py -v

# With parallel execution
pytest tests/ -n 4 -m smoke -v
```

## 🔧 Configuration

### Environment Configuration

Edit `config/environments.yaml` to add/modify environments:

```yaml
qa:
  base_url: "https://qa.example.com"
  api_base_url: "https://api-qa.example.com"
  credentials:
    standard:
      username: "user@test.com"
      password: "password"
```

### Feature Flags (.env)

```bash
SELF_HEALING=true          # Enable AI self-healing
AI_ANALYSIS=true           # Enable failure analysis
VIDEO_RECORDING=onfailure  # Video recording mode
PARALLEL_WORKERS=4         # Number of parallel workers
```

## 🐳 Docker Usage

```bash
# Build and run
cd ci_cd/docker
docker-compose up test-runner

# View Allure report
docker-compose up allure-server
# Access at http://localhost:5050
```

## 📊 CI/CD Integration

### Jenkins

1. Copy `ci_cd/Jenkinsfile` to your Jenkins pipeline
2. Configure parameters in Jenkins
3. Run pipeline

### GitHub Actions

1. Copy workflows from `ci_cd/.github/workflows/` to `.github/workflows/`
2. Push to GitHub
3. Workflows will run automatically

## 🤖 AI Self-Healing

The framework automatically heals broken locators using:

1. **Text-based healing** - Finds elements by text content
2. **Attribute-based healing** - Uses stable attributes
3. **AI-based healing** - Machine learning predictions

Healing events are logged and reported in Allure.

## 📈 Reporting

### Allure Report

```bash
# Generate and open
allure serve reports/allure-results

# Generate only
allure generate reports/allure-results -o reports/allure-report --clean
```

### HTML Report

Generated automatically at `reports/report.html`

## 🧪 Writing Tests

### UI Test Example

```python
import pytest
from business.ui.pages.login_page import LoginPage

@pytest.mark.ui
@pytest.mark.smoke
def test_login(login_page: LoginPage):
    login_page.open()
    login_page.login("user@test.com", "password")
    assert login_page.is_logged_in()
```

### API Test Example

```python
import pytest
from business.api.endpoints.user_endpoint import UserEndpoint

@pytest.mark.api
def test_get_user(user_endpoint: UserEndpoint):
    user = user_endpoint.get_user(1)
    assert user["id"] == 1
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Playwright browsers not installed
```bash
Solution: playwright install --with-deps
```

**Issue**: Permission denied on scripts
```bash
Solution: chmod +x scripts/*.sh
```

**Issue**: Module not found
```bash
Solution: source venv/bin/activate && pip install -r requirements.txt
```

**Issue**: Tests failing with timeout
```bash
Solution: Increase timeout in config/environments.yaml
```

## 📚 Documentation

- [Playwright Docs](https://playwright.dev/python/)
- [Pytest Docs](https://docs.pytest.org/)
- [Allure Docs](https://docs.qameta.io/allure/)

## 💡 Best Practices

1. **Use Page Objects** - Keep locators in page classes
2. **Use Fixtures** - Leverage pytest fixtures for setup
3. **Mark Tests** - Use pytest markers (@pytest.mark.smoke)
4. **Parametrize** - Use @pytest.mark.parametrize for data-driven tests
5. **Self-Healing** - Give elements logical names for healing
6. **Async Updates** - Update page objects when healing occurs

## 🆘 Support

For issues or questions:
- Check logs in `reports/logs/`
- Review Allure report for details
- Check self-healing notifications

## 📝 License

MIT License - Feel free to use and modify

## 🎉 Happy Testing!

The framework is ready to use. Start by running smoke tests and explore from there!
