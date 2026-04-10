# Patient Account Creation and Login API

This module implements the patient account creation and login flow extracted from the Postman collection.

## Overview

The patient API provides functionality for:
- Patient account registration with MFA verification
- Username reservation
- Email-based MFA code delivery
- Patient login via SSO
- Consent management

## Architecture

### Schemas (`business/api/schemas/patient_schema.py`)

Pydantic models for request/response validation:

- **ReserveUsernameRequest/Response** - Username reservation with client key
- **MFAEmailRequest** - MFA verification email request
- **CreateUserRequest** - Complete user creation payload
- **UserCreationData** - User profile data
- **PatientData** - Patient-specific information
- **ConsentResult** - User consent acceptance
- **RecaptchaKeyResponse** - Recaptcha key for registration
- **DEFAULT_CONSENTS** - Pre-configured consents by country (GB, US, CA)

### Endpoints (`business/api/endpoints/patient_endpoint.py`)

API endpoint implementations:

#### PatientEndpoint Class

**Methods:**

1. **`get_consents(country, language, role)`**
   - Retrieves patient consents for a specific country
   - Endpoint: `GET /patient/consents`
   - Returns: List of consent objects

2. **`reserve_username(username)`**
   - Reserves a username and obtains client key for MFA
   - Endpoint: `POST /patient/orders/reserve/username`
   - Returns: Client key string

3. **`request_mfa_email(username, email, first_name, last_name, country, language)`**
   - Requests MFA verification code via email
   - Endpoint: `POST /patient/orders/mfa/email/reg`
   - Returns: Boolean success status

4. **`get_recaptcha_key()`**
   - Retrieves recaptcha key for user registration
   - Endpoint: `GET /patient/configuration/recaptcha/key`
   - Returns: Recaptcha key string

5. **`create_user(username, password, email, first_name, last_name, country, mfa_code, ...)`**
   - Creates a new patient user account
   - Endpoint: `POST /patient/users?type=PATIENT`
   - Returns: User creation response data

6. **`initiate_sso_login(country, language)`**
   - Initiates SSO login flow
   - Endpoint: `GET /patient/sso/login`
   - Returns: Authorization URL

7. **`create_account_full_flow(username, password, first_name, last_name, country, mfa_code, ...)`**
   - Executes complete account creation flow
   - Combines all steps above
   - Returns: Dictionary with account details

**Helper Methods:**

- `generate_username(prefix)` - Generates unique username with timestamp
- `generate_random_name()` - Returns random first and last names

## Tests (`tests/api/test_patient_login.py`)

### Test Suite: TestPatientLogin

#### Test Cases

1. **`test_patient_login_existing_account`**
   - Tests login with existing credentials from `environments.yaml`
   - Marks: `@pytest.mark.api`, `@pytest.mark.smoke`

2. **`test_patient_login_conditional`**
   - Parametrized test for new vs existing account
   - Parameters: `create_new_account` (True/False)
   - Marks: `@pytest.mark.api`

3. **`test_complete_account_creation_with_mfa`**
   - Tests full account creation with MFA code
   - Requires `--mfa-code` pytest option
   - Marks: `@pytest.mark.api`, `@pytest.mark.integration`

4. **`test_get_patient_consents`**
   - Tests consent retrieval for different countries
   - Parametrized: GB, US, CA
   - Marks: `@pytest.mark.api`

5. **`test_reserve_username`**
   - Tests username reservation
   - Marks: `@pytest.mark.api`

6. **`test_get_recaptcha_key`**
   - Tests recaptcha key retrieval
   - Marks: `@pytest.mark.api`

### Custom Pytest Options

```bash
--mfa-code <code>        # MFA code for account creation test
--create-account         # Create new account instead of using existing
```

## Usage Examples

### Example 1: Create New Account (Requires MFA Code)

```python
from core.api_client import APIClient
from business.api.endpoints.patient_endpoint import PatientEndpoint

# Initialize
api_client = APIClient(base_url="https://carelink-stage1-next.minimed.eu")
patient_endpoint = PatientEndpoint(api_client)

# Generate account details
username = patient_endpoint.generate_username()
first_name, last_name = patient_endpoint.generate_random_name()

# Execute full flow (MFA code must be obtained from email)
result = patient_endpoint.create_account_full_flow(
    username=username,
    password="PostmanUser2023!",
    first_name=first_name,
    last_name=last_name,
    country="GB",
    mfa_code="123456",  # From email
    zip_code="HP5 4UX"
)

print(f"Account created: {result['username']}")
```

### Example 2: Login with Existing Account

```python
from core.api_client import APIClient
from business.api.endpoints.patient_endpoint import PatientEndpoint
from config.config import config

# Initialize
api_client = APIClient(base_url=config.get_base_url())
patient_endpoint = PatientEndpoint(api_client)

# Get credentials from config
credentials = config.get_credentials("standard")

# Initiate SSO login
authorize_url = patient_endpoint.initiate_sso_login(country="GB")
print(f"Login URL: {authorize_url}")
```

### Example 3: Individual Steps

```python
# Step-by-step account creation
patient_endpoint = PatientEndpoint(api_client)

# 1. Get consents
consents = patient_endpoint.get_consents(country="GB")

# 2. Reserve username
username = "PMP1234567890"
client_key = patient_endpoint.reserve_username(username)

# 3. Request MFA email
patient_endpoint.request_mfa_email(
    username=username,
    email=f"{username}@carelink.testinator.com",
    first_name="John",
    last_name="Doe",
    country="GB"
)

# 4. Get recaptcha key
recaptcha_key = patient_endpoint.get_recaptcha_key()

# 5. Create user (with MFA code from email)
user_response = patient_endpoint.create_user(
    username=username,
    password="PostmanUser2023!",
    email=f"{username}@carelink.testinator.com",
    first_name="John",
    last_name="Doe",
    country="GB",
    mfa_code="123456"  # From email
)
```

## Running Tests

### Run all patient login tests
```bash
pytest tests/api/test_patient_login.py -v
```

### Run with existing account only
```bash
pytest tests/api/test_patient_login.py::TestPatientLogin::test_patient_login_existing_account -v
```

### Run with new account creation (requires MFA)
```bash
pytest tests/api/test_patient_login.py::TestPatientLogin::test_complete_account_creation_with_mfa --mfa-code=123456 -v
```

### Run smoke tests
```bash
pytest tests/api/test_patient_login.py -m smoke -v
```

### Run with Allure reporting
```bash
pytest tests/api/test_patient_login.py --alluredir=reports/allure-results
allure serve reports/allure-results
```

## Configuration

Update `config/environments.yaml` with patient credentials:

```yaml
staging:
  base_url: "https://carelink-stage1-next.minimed.eu"
  
  credentials:
    standard:
      username: "PMP1762376204"
      password: "PostmanUser2023!"
  
  country_code: "GB"  # Optional: GB, US, CA
```

## API Flow Diagram

```
1. Get Consents
   └─> GET /patient/consents?country={country}

2. Reserve Username
   └─> POST /patient/orders/reserve/username
       └─> Returns: clientKey

3. Request MFA Email
   └─> POST /patient/orders/mfa/email/reg
       └─> Headers: CLIENT_KEY
       └─> Sends email with MFA code

4. Get Recaptcha Key
   └─> GET /patient/configuration/recaptcha/key
       └─> Returns: recaptcha key

5. Create User
   └─> POST /patient/users?type=PATIENT
       └─> Headers: Client_key
       └─> Body: mfaCode, captchaCode, userData, patientData
       └─> Returns: 201 Created

6. Login (SSO)
   └─> GET /patient/sso/login?country={country}
       └─> Returns: 303 with authorize URL
```

## Important Notes

### MFA Code Retrieval

The current implementation requires manual MFA code input or integration with Mailinator API. The Postman collection uses:

- **Email domain**: `carelink.testinator.com`
- **Mailinator API**: To retrieve MFA codes from test emails
- **Bearer token**: Required for Mailinator API access

To fully automate, you would need to:
1. Integrate Mailinator API or similar email testing service
2. Parse MFA code from email body
3. Pass code to `create_user()` method

### Password Encoding

Passwords are automatically base64 encoded by the `create_user()` method. Pass plain text passwords.

### Country-Specific Consents

Default consents are pre-configured for:
- **GB (EMEA)**: TOU_EMEA_1, PS_EMEA_1, DR_EMEA_1
- **US**: TOU_US, PS_US, DR_US
- **CA (Canada)**: TOU_CANADA, PS_CANADA, DR_CANADA, AGGREGATE_CANADA, SMS_TEXT_CANADA

### OAuth/SSO Flow

The complete login flow requires:
1. Initiate SSO (`/patient/sso/login`)
2. Follow OAuth redirects
3. Submit credentials to auth provider
4. Handle callback with authorization code
5. Exchange code for access token

Currently, only step 1 is implemented. Full OAuth flow requires additional endpoints or browser automation.

## Troubleshooting

### Issue: "Client key not set"
**Solution**: Call `reserve_username()` before `request_mfa_email()` or `create_user()`

### Issue: "MFA code required"
**Solution**: Retrieve MFA code from email (manual or via Mailinator API) and pass to `create_user()`

### Issue: "Recaptcha key not found"
**Solution**: Call `get_recaptcha_key()` before `create_user()` or use `create_account_full_flow()`

### Issue: "Username already exists"
**Solution**: Use `generate_username()` to create unique usernames with timestamps

## Future Enhancements

- [ ] Mailinator API integration for automated MFA retrieval
- [ ] Complete OAuth/SSO login flow implementation
- [ ] Auth token management and refresh
- [ ] Account deletion/cleanup utilities
- [ ] Additional country support
- [ ] Phone-based MFA option
- [ ] Care partner account creation
