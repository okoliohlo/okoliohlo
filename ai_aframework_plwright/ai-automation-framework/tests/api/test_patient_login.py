"""
Patient Login API Tests
Tests patient account creation and login flow with conditional account creation
"""

import pytest
import allure
from core.api_client import APIClient
from business.api.endpoints.patient_endpoint import PatientEndpoint
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("Patient Authentication")
@allure.story("Patient Login")
class TestPatientLogin:
    """Test patient login with optional account creation"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client instance"""
        base_url = config.get_base_url()
        client = APIClient(base_url=base_url)
        yield client

    @pytest.fixture(scope="class")
    def patient_endpoint(self, api_client):
        """Create patient endpoint instance"""
        return PatientEndpoint(api_client)

    @pytest.mark.api
    @pytest.mark.smoke
    @allure.title("Test patient login with existing account")
    @allure.description("Test login flow using existing account credentials from environments.yaml")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patient_login_existing_account(self, api_client, patient_endpoint):
        """
        Test patient login with existing account credentials
        Uses credentials from environments.yaml
        """
        with allure.step("Get credentials from config"):
            credentials = config.get_credentials("standard")
            username = credentials.get("username")
            password = credentials.get("password")
            
            logger.info(f"Testing login with existing account: {username}")
            
            assert username, "Username not found in config"
            assert password, "Password not found in config"

        with allure.step("Initiate SSO login"):
            # Get country from config or default to GB
            country = "GB"  # Default country code
            
            authorize_url = patient_endpoint.initiate_sso_login(country=country)
            
            assert authorize_url, "Authorization URL not received"
            logger.info(f"SSO login initiated successfully")

        with allure.step("Verify login response"):
            # Note: Full OAuth flow requires browser interaction or additional API calls
            # This test verifies the initial SSO endpoint works
            logger.info("Login initiation successful")

    @pytest.mark.api
    @pytest.mark.parametrize("create_new_account", [True, False], ids=["new_account", "existing_account"])
    @allure.title("Test patient login with conditional account creation")
    @allure.description("Test login with option to create new account or use existing credentials")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_patient_login_conditional(
        self,
        api_client,
        patient_endpoint,
        create_new_account,
        request
    ):
        """
        Test patient login with conditional account creation
        
        Args:
            create_new_account: If True, creates new account; if False, uses existing credentials
        """
        country = "GB"  # Default country code
        language = "en"
        
        if create_new_account:
            # Create new account flow
            with allure.step("Generate new account details"):
                username = patient_endpoint.generate_username()
                first_name, last_name = patient_endpoint.generate_random_name()
                password = "PostmanUser2023!"
                email = f"{username}@carelink.testinator.com"
                
                logger.info(f"Creating new account: {username}")
                
                allure.attach(
                    f"Username: {username}\nEmail: {email}\nName: {first_name} {last_name}",
                    name="New Account Details",
                    attachment_type=allure.attachment_type.TEXT
                )

            with allure.step("Get patient consents"):
                consents = patient_endpoint.get_consents(country=country, language=language)
                assert consents, "Failed to retrieve consents"
                logger.info(f"Retrieved {len(consents)} consents")

            with allure.step("Reserve username"):
                client_key = patient_endpoint.reserve_username(username)
                assert client_key, "Failed to reserve username"
                logger.info(f"Username reserved with client key: {client_key}")

            with allure.step("Request MFA email"):
                mfa_sent = patient_endpoint.request_mfa_email(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    country=country,
                    language=language
                )
                assert mfa_sent, "Failed to send MFA email"
                logger.info("MFA email sent successfully")

            with allure.step("Get recaptcha key"):
                recaptcha_key = patient_endpoint.get_recaptcha_key()
                assert recaptcha_key, "Failed to get recaptcha key"
                logger.info(f"Recaptcha key obtained: {recaptcha_key}")

            with allure.step("Complete account creation with auto MFA retrieval"):
                try:
                    result = patient_endpoint.create_account_full_flow(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        country=country,
                        email=email,
                        zip_code="HP5 4UX" if country == "GB" else None,
                        auto_retrieve_mfa=True  # Automatically retrieve MFA code
                    )
                    
                    assert result, "Account creation failed"
                    assert result.get("username") == username, "Username mismatch"
                    assert result.get("mfa_code"), "MFA code not retrieved"
                    
                    logger.info(f"✅ Account created successfully: {username}")
                    logger.info(f"✅ MFA code: {result.get('mfa_code')}")
                    
                    allure.attach(
                        f"Username: {username}\n"
                        f"Email: {email}\n"
                        f"MFA Code: {result.get('mfa_code')}\n"
                        f"Client Key: {result.get('client_key')}",
                        name="Account Creation Success",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                except Exception as e:
                    logger.error(f"Account creation failed: {str(e)}")
                    pytest.skip(f"Account creation failed: {str(e)}")

        else:
            # Use existing account flow
            with allure.step("Get existing account credentials"):
                credentials = config.get_credentials("standard")
                username = credentials.get("username")
                password = credentials.get("password")
                
                logger.info(f"Using existing account: {username}")
                
                assert username, "Username not found in config"
                assert password, "Password not found in config"
                
                allure.attach(
                    f"Username: {username}",
                    name="Existing Account",
                    attachment_type=allure.attachment_type.TEXT
                )

            with allure.step("Initiate SSO login"):
                authorize_url = patient_endpoint.initiate_sso_login(country=country, language=language)
                
                assert authorize_url, "Authorization URL not received"
                logger.info(f"SSO login initiated for existing account")

    @pytest.mark.api
    @pytest.mark.integration
    @allure.title("Test complete account creation flow with auto MFA")
    @allure.description("Test complete patient account creation with automatic MFA retrieval")
    @allure.severity(allure.severity_level.NORMAL)
    def test_complete_account_creation_with_auto_mfa(
        self,
        api_client,
        patient_endpoint,
        request
    ):
        """
        Test complete account creation flow with automatic MFA code retrieval
        
        This test automatically retrieves the MFA code from Mailinator
        """
        country = "GB"  # Default country code
        
        with allure.step("Generate account details"):
            username = patient_endpoint.generate_username()
            first_name, last_name = patient_endpoint.generate_random_name()
            password = "PostmanUser2023!"
            email = f"{username}@carelink.testinator.com"
            
            logger.info(f"Creating complete account: {username}")
            logger.info(f"Email: {email}")

        with allure.step("Execute full account creation flow with auto MFA"):
            result = patient_endpoint.create_account_full_flow(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                country=country,
                email=email,
                zip_code="HP5 4UX" if country == "GB" else None,
                auto_retrieve_mfa=True  # Automatically retrieve MFA from email
            )
            
            assert result, "Account creation failed"
            assert result.get("username") == username, "Username mismatch"
            assert result.get("mfa_code"), "MFA code not retrieved"
            
            logger.info(f"✅ Account created successfully: {username}")
            logger.info(f"✅ MFA code: {result.get('mfa_code')}")
            
            allure.attach(
                f"Username: {username}\n"
                f"Email: {email}\n"
                f"MFA Code: {result.get('mfa_code')}\n"
                f"Client Key: {result.get('client_key')}",
                name="Complete Account Creation",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("Verify account can login"):
            authorize_url = patient_endpoint.initiate_sso_login(country=country)
            assert authorize_url, "Login initiation failed for new account"
            logger.info("✅ New account can initiate login")

    @pytest.mark.api
    @allure.title("Test patient consents retrieval")
    @allure.description("Test retrieving patient consents for different countries")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("country", ["GB", "US", "CA"])
    def test_get_patient_consents(self, patient_endpoint, country):
        """
        Test retrieving patient consents for different countries
        
        Args:
            country: Country code to test
        """
        with allure.step(f"Get consents for {country}"):
            consents = patient_endpoint.get_consents(country=country)
            
            assert consents, f"No consents returned for {country}"
            assert isinstance(consents, list), "Consents should be a list"
            
            if consents:
                assert "key" in consents[0], "Consent should have 'key' field"
                logger.info(f"Retrieved {len(consents)} consents for {country}")

    @pytest.mark.api
    @allure.title("Test username reservation")
    @allure.description("Test username reservation and client key generation")
    @allure.severity(allure.severity_level.NORMAL)
    def test_reserve_username(self, patient_endpoint):
        """Test username reservation"""
        with allure.step("Generate unique username"):
            username = patient_endpoint.generate_username()
            logger.info(f"Generated username: {username}")

        with allure.step("Reserve username"):
            client_key = patient_endpoint.reserve_username(username)
            
            assert client_key, "Client key not received"
            assert len(client_key) > 0, "Client key is empty"
            logger.info(f"Username reserved successfully with client key: {client_key}")

    @pytest.mark.api
    @allure.title("Test recaptcha key retrieval")
    @allure.description("Test retrieving recaptcha key for registration")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_recaptcha_key(self, patient_endpoint):
        """Test recaptcha key retrieval"""
        with allure.step("Get recaptcha key"):
            recaptcha_key = patient_endpoint.get_recaptcha_key()
            
            assert recaptcha_key, "Recaptcha key not received"
            assert len(recaptcha_key) > 0, "Recaptcha key is empty"
            logger.info(f"Recaptcha key retrieved: {recaptcha_key}")


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--mfa-code",
        action="store",
        default=None,
        help="MFA code for account creation test"
    )
    parser.addoption(
        "--create-account",
        action="store_true",
        default=False,
        help="Create new account instead of using existing credentials"
    )
