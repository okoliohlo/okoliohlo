"""
Patient Account Creation and Management Endpoints
Implements the patient registration and login flow from Postman collection
"""

import time
import base64
import random
from typing import Optional, Dict, Any
from datetime import datetime
from core.api_client import APIClient
from business.api.schemas.patient_schema import (
    ReserveUsernameRequest,
    ReserveUsernameResponse,
    MFAEmailRequest,
    CreateUserRequest,
    UserCreationData,
    PatientData,
    ConsentResult,
    RecaptchaKeyResponse,
    DEFAULT_CONSENTS
)
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class PatientEndpoint:
    """
    Patient account creation and management endpoints
    """

    def __init__(self, api_client: APIClient):
        """
        Initialize patient endpoint
        
        Args:
            api_client: APIClient instance
        """
        self.client = api_client
        self.client_key = None
        self.mfa_code = None
        self.recaptcha_code = None
        self.auth_token = None
        self.refresh_token = None
        self.session_cookies = {}

    @allure.step("Get patient consents for country: {country}")
    def get_consents(self, country: str, language: str = "en", role: str = "PATIENT") -> Dict[str, Any]:
        """
        Get patient consents for a specific country
        
        Args:
            country: Country code (e.g., GB, US, CA)
            language: Language code
            role: User role
            
        Returns:
            Response with consents
        """
        logger.info(f"Getting consents for country: {country}")
        
        response = self.client.get(
            "/patient/consents",
            params={
                "country": country,
                "language": language,
                "role": role
            }
        )
        
        self.client.validate_status_code(response, 200)
        return response.json()

    @allure.step("Reserve username: {username}")
    def reserve_username(self, username: str) -> str:
        """
        Reserve a username and get client key for MFA
        
        Args:
            username: Username to reserve
            
        Returns:
            Client key for MFA verification
        """
        logger.info(f"Reserving username: {username}")
        
        request_data = ReserveUsernameRequest(username=username)
        
        response = self.client.post(
            "/patient/orders/reserve/username",
            json_data=request_data.dict(),
            headers={
                "Content-Type": "application/json; charset=utf-8"
            }
        )
        
        self.client.validate_status_code(response, 200)
        
        response_data = ReserveUsernameResponse(**response.json())
        self.client_key = response_data.clientKey
        
        logger.info(f"Username reserved. Client key: {self.client_key}")
        return self.client_key

    @allure.step("Request MFA email for: {email}")
    def request_mfa_email(
        self,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        country: str,
        language: str = "en"
    ) -> bool:
        """
        Request MFA verification code via email
        
        Args:
            username: Username
            email: Email address
            first_name: First name
            last_name: Last name
            country: Country code
            language: Language code
            
        Returns:
            True if MFA email sent successfully
        """
        if not self.client_key:
            raise ValueError("Client key not set. Call reserve_username first.")
        
        logger.info(f"Requesting MFA email for: {email}")
        
        request_data = MFAEmailRequest(
            country=country,
            email=email,
            firstName=first_name,
            language=language,
            lastName=last_name,
            username=username
        )
        
        response = self.client.post(
            "/patient/orders/mfa/email/reg",
            json_data=request_data.dict(),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "CLIENT_KEY": self.client_key,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        
        self.client.validate_status_code(response, 204)
        logger.info("MFA email sent successfully")
        return True

    @allure.step("Get recaptcha key")
    def get_recaptcha_key(self) -> str:
        """
        Get recaptcha key for user registration
        
        Returns:
            Recaptcha key value
        """
        logger.info("Getting recaptcha key")
        
        response = self.client.get(
            "/patient/configuration/recaptcha/key",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json; charset=utf-8"
            }
        )
        
        self.client.validate_status_code(response, 200)
        
        response_data = RecaptchaKeyResponse(**response.json())
        self.recaptcha_code = response_data.value
        
        logger.info(f"Recaptcha key obtained: {self.recaptcha_code}")
        return self.recaptcha_code

    @allure.step("Create patient user: {username}")
    def create_user(
        self,
        username: str,
        password: str,
        email: str,
        first_name: str,
        last_name: str,
        country: str,
        mfa_code: str,
        phone_number: str = "+16619999999",
        zip_code: Optional[str] = None,
        language: str = "en",
        consents: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create a new patient user account
        
        Args:
            username: Username
            password: Password (will be base64 encoded)
            email: Email address
            first_name: First name
            last_name: Last name
            country: Country code
            mfa_code: MFA verification code
            phone_number: Phone number
            zip_code: Zip/postal code
            language: Language code
            consents: List of consent results (uses defaults if None)
            
        Returns:
            Response data from user creation
        """
        if not self.client_key:
            raise ValueError("Client key not set. Call reserve_username first.")
        
        if not self.recaptcha_code:
            self.get_recaptcha_key()
        
        logger.info(f"Creating patient user: {username}")
        
        # Encode password to base64
        encoded_password = base64.b64encode(password.encode()).decode()
        
        # Use default consents if not provided
        if consents is None:
            consents = DEFAULT_CONSENTS.get(country, DEFAULT_CONSENTS["GB"])
        
        # Build consent results
        consent_results = [ConsentResult(**consent) for consent in consents]
        
        # Build user data
        user_data = UserCreationData(
            username=username,
            password=encoded_password,
            emailAddress=email,
            guardianParent=False,
            twoFaRequired=False,
            firstName=first_name,
            lastName=last_name,
            phoneNumber=phone_number,
            consentResults=consent_results,
            country=country,
            language=language
        )
        
        # Build patient data
        patient_data = PatientData(
            zip=zip_code,
            therapyType=None,
            diabetesType=None,
            gender=None
        )
        
        # Build request
        request_data = CreateUserRequest(
            mfaCode=mfa_code,
            captchaCode=self.recaptcha_code,
            data=user_data,
            patient=patient_data
        )
        
        response = self.client.post(
            "/patient/users",
            params={"type": "PATIENT"},
            json_data=request_data.dict(),
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "Client_key": self.client_key,
                "Referer": f"{self.client.base_url}/app/mfa?registration=true"
            }
        )
        
        self.client.validate_status_code(response, 201)
        logger.info(f"Patient user created successfully: {username}")
        
        return response.json() if response.text else {}

    @allure.step("Initiate SSO login")
    def initiate_sso_login(self, country: str, language: str = "en") -> str:
        """
        Initiate SSO login flow
        
        Args:
            country: Country code
            language: Language code
            
        Returns:
            Authorization URL
        """
        logger.info("Initiating SSO login")
        
        response = self.client.get(
            "/patient/sso/login",
            params={
                "country": country,
                "lang": language
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            },
            allow_redirects=False
        )
        
        self.client.validate_status_code(response, 303)
        
        authorize_url = response.headers.get('location')
        logger.info(f"SSO login initiated. Authorize URL: {authorize_url}")
        
        # Store session cookies
        self._store_cookies(response.cookies)
        
        return authorize_url

    @allure.step("Complete OAuth login flow")
    def complete_oauth_login_flow(
        self,
        username: str,
        password: str,
        country: str = "GB",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Complete full OAuth login flow based on Postman collection
        
        Steps:
        1. Initiate SSO login → get authorize_url
        2. GET authorize_url → get login_state_url and state
        3. GET login_state_url → display login page
        4. POST credentials to login_state_url → get resumed_state
        5. GET /authorize/resume → get authorization code
        6. GET /patient/sso/auth with code → complete authentication
        
        Args:
            username: Patient username
            password: Patient password
            country: Country code
            language: Language code
            
        Returns:
            Authentication response with tokens and cookies
        """
        import urllib.parse
        import re
        
        logger.info(f"Starting complete OAuth login flow for user: {username}")
        
        # Step 1: Initiate SSO login
        logger.info("Step 1: Initiating SSO login")
        authorize_url = self.initiate_sso_login(country=country, language=language)
        
        if not authorize_url:
            raise Exception("Failed to get authorize URL")
        
        logger.info(f"Authorize URL: {authorize_url[:100]}...")
        
        # Step 2: GET authorize_url to get login page redirect
        logger.info("Step 2: Following authorize URL")
        # Use requests directly for external URL
        import requests
        response = requests.get(
            authorize_url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br"
            },
            cookies=self.session_cookies,
            allow_redirects=False,
            verify=False
        )
        
        self.client.validate_status_code(response, 302)
        self._store_cookies(response.cookies)
        
        # Extract login_state_url from Location header
        login_redirect = response.headers.get('location')
        if not login_redirect:
            raise Exception("No location header in authorize response")
        
        # Parse the authorize_url to get base URL
        auth_parsed = urllib.parse.urlparse(authorize_url)
        login_base_url = f"{auth_parsed.scheme}://{auth_parsed.netloc}"
        
        # Handle relative or absolute redirect
        if login_redirect.startswith('http'):
            login_state_url = login_redirect
            parsed_url = urllib.parse.urlparse(login_redirect)
        else:
            # Relative URL - prepend base URL
            login_state_url = f"{login_base_url}{login_redirect}"
            parsed_url = urllib.parse.urlparse(login_state_url)
        
        # Parse state from redirect URL
        query_params = urllib.parse.parse_qs(parsed_url.query)
        state = query_params.get('state', [None])[0]
        
        if not state:
            raise Exception("No state parameter in redirect URL")
        
        logger.info(f"State: {state}")
        logger.info(f"Login state URL: {login_state_url[:100]}...")
        
        # Step 3: GET login page
        logger.info("Step 3: Loading login page")
        response = requests.get(
            login_state_url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br"
            },
            cookies=self.session_cookies,
            allow_redirects=False,
            verify=False
        )
        
        self.client.validate_status_code(response, 200)
        self._store_cookies(response.cookies)
        
        # Step 4: POST credentials
        logger.info("Step 4: Submitting credentials")
        login_data = {
            "locale": language,
            "action": "default",
            "username": username,
            "password": password,
            "state": state
        }
        
        response = requests.post(
            login_state_url,
            data=login_data,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": login_state_url
            },
            cookies=self.session_cookies,
            allow_redirects=False,
            verify=False
        )
        
        self.client.validate_status_code(response, 302)
        self._store_cookies(response.cookies)
        
        # Extract resumed_state from Location header
        resume_redirect = response.headers.get('location')
        if not resume_redirect:
            raise Exception("No location header after login POST")
        
        parsed_resume = urllib.parse.urlparse(resume_redirect)
        resume_params = urllib.parse.parse_qs(parsed_resume.query)
        resumed_state = resume_params.get('state', [None])[0]
        
        if not resumed_state:
            raise Exception("No resumed state in redirect")
        
        logger.info(f"Resumed state: {resumed_state}")
        
        # Step 5: GET /authorize/resume to get authorization code
        logger.info("Step 5: Getting authorization code")
        resume_url = f"{login_base_url}/authorize/resume?state={resumed_state}"
        
        response = requests.get(
            resume_url,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": login_state_url
            },
            cookies=self.session_cookies,
            allow_redirects=False,
            verify=False
        )
        
        self.client.validate_status_code(response, 302)
        self._store_cookies(response.cookies)
        
        # Extract authorization code from Location header
        code_redirect = response.headers.get('location')
        if not code_redirect:
            raise Exception("No location header in resume response")
        
        parsed_code = urllib.parse.urlparse(code_redirect)
        code_params = urllib.parse.parse_qs(parsed_code.query)
        auth_code = code_params.get('code', [None])[0]
        
        if not auth_code:
            raise Exception("No authorization code in redirect")
        
        logger.info(f"Authorization code: {auth_code[:20]}...")
        
        # Step 6: Complete SSO auth with authorization code
        logger.info("Step 6: Completing SSO authentication")
        response = self.client.get(
            "/patient/sso/auth",
            params={
                "code": auth_code,
                "state": "auth"
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            },
            allow_redirects=False
        )
        
        # Status could be 307 (redirect) or 302
        if response.status_code not in [302, 307]:
            logger.warning(f"Unexpected status code: {response.status_code}")
        
        # Extract and store all cookies
        self._store_cookies(response.cookies)
        
        # Look for auth token in cookies
        for cookie_name in ['auth_tmp_token', 'c_token_valid', 'auth_token']:
            if cookie_name in response.cookies:
                self.auth_token = response.cookies[cookie_name]
                self.client.set_auth_token(self.auth_token)
                logger.info(f"Auth token found in cookie '{cookie_name}': {self.auth_token[:20]}...")
                break
        
        logger.info("OAuth login flow completed successfully")
        logger.info(f"Total cookies captured: {len(self.session_cookies)}")
        
        return {
            "status_code": response.status_code,
            "auth_token": self.auth_token,
            "auth_code": auth_code,
            "cookies": self.session_cookies.copy(),
            "username": username
        }
    
    @allure.step("Complete SSO authentication")
    def complete_sso_auth(self, authorization_code: str) -> Dict[str, Any]:
        """
        Complete SSO authentication with authorization code
        
        Args:
            authorization_code: OAuth authorization code from callback
            
        Returns:
            Authentication response with tokens
        """
        logger.info("Completing SSO authentication")
        
        response = self.client.get(
            "/patient/sso/auth",
            params={
                "code": authorization_code,
                "state": "auth"
            },
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            },
            allow_redirects=False
        )
        
        # Extract auth token from cookies
        if 'auth_tmp_token' in response.cookies:
            self.auth_token = response.cookies['auth_tmp_token']
            self.client.set_auth_token(self.auth_token)
            logger.info(f"Auth token stored: {self.auth_token[:20]}...")
        
        # Store all session cookies
        self._store_cookies(response.cookies)
        
        return {
            "status_code": response.status_code,
            "auth_token": self.auth_token,
            "cookies": dict(response.cookies)
        }

    def _store_cookies(self, cookies):
        """
        Store session cookies
        
        Args:
            cookies: RequestsCookieJar or dict of cookies
        """
        if cookies:
            for key, value in cookies.items():
                self.session_cookies[key] = value
                logger.debug(f"Stored cookie: {key}")

    @allure.step("Get stored auth token")
    def get_auth_token(self) -> Optional[str]:
        """
        Get stored authentication token
        
        Returns:
            Auth token if available, None otherwise
        """
        return self.auth_token

    @allure.step("Set auth token")
    def set_auth_token(self, token: str):
        """
        Set authentication token
        
        Args:
            token: Authentication token
        """
        self.auth_token = token
        self.client.set_auth_token(token)
        logger.info("Auth token set successfully")

    @allure.step("Get session cookies")
    def get_session_cookies(self) -> Dict[str, str]:
        """
        Get all stored session cookies
        
        Returns:
            Dictionary of session cookies
        """
        return self.session_cookies.copy()

    @allure.step("Save token to file")
    def save_token_to_file(self, filepath: str):
        """
        Save authentication token to file
        
        Args:
            filepath: Path to save token file
        """
        import json
        from pathlib import Path
        
        token_data = {
            "auth_token": self.auth_token,
            "refresh_token": self.refresh_token,
            "client_key": self.client_key,
            "cookies": self.session_cookies,
            "timestamp": time.time()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(token_data, f, indent=2)
        
        logger.info(f"Token saved to: {filepath}")

    @allure.step("Load token from file")
    def load_token_from_file(self, filepath: str) -> bool:
        """
        Load authentication token from file
        
        Args:
            filepath: Path to token file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        import json
        from pathlib import Path
        
        if not Path(filepath).exists():
            logger.warning(f"Token file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                token_data = json.load(f)
            
            self.auth_token = token_data.get("auth_token")
            self.refresh_token = token_data.get("refresh_token")
            self.client_key = token_data.get("client_key")
            self.session_cookies = token_data.get("cookies", {})
            
            if self.auth_token:
                self.client.set_auth_token(self.auth_token)
            
            logger.info(f"Token loaded from: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load token: {str(e)}")
            return False

    @allure.step("Get MFA code from email")
    def get_mfa_code_from_email(
        self,
        email: str,
        max_wait_seconds: int = 60
    ) -> Optional[str]:
        """
        Automatically retrieve MFA code from Mailinator email
        
        Args:
            email: Email address (must be @mailinator.com or @carelink.testinator.com)
            max_wait_seconds: Maximum time to wait for email
            
        Returns:
            MFA code if found, None otherwise
        """
        from utilities.mailinator_helper import get_mfa_code_from_email
        
        logger.info(f"Retrieving MFA code from email: {email}")
        
        # Convert carelink.testinator.com to mailinator.com if needed
        if "@carelink.testinator.com" in email:
            email = email.replace("@carelink.testinator.com", "@mailinator.com")
        
        mfa_code = get_mfa_code_from_email(email, max_wait_seconds)
        
        if mfa_code:
            logger.info(f"✅ MFA code retrieved: {mfa_code}")
        else:
            logger.error("❌ Failed to retrieve MFA code")
        
        return mfa_code

    @allure.step("Complete patient account creation flow with auto MFA")
    def create_account_full_flow(
        self,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        country: str,
        mfa_code: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: str = "+16619999999",
        zip_code: Optional[str] = None,
        language: str = "en",
        auto_retrieve_mfa: bool = True
    ) -> Dict[str, Any]:
        """
        Complete patient account creation flow with automatic MFA retrieval
        
        Args:
            username: Username
            password: Password
            first_name: First name
            last_name: Last name
            country: Country code
            mfa_code: MFA verification code (if None and auto_retrieve_mfa=True, will fetch automatically)
            email: Email address (defaults to username@carelink.testinator.com)
            phone_number: Phone number
            zip_code: Zip/postal code
            language: Language code
            auto_retrieve_mfa: If True, automatically retrieve MFA code from email
            
        Returns:
            Dict with account creation details
        """
        if email is None:
            email = f"{username}@carelink.testinator.com"
        
        logger.info(f"Starting full account creation flow for: {username}")
        
        # Step 1: Get consents
        consents = self.get_consents(country, language)
        
        # Step 2: Reserve username
        client_key = self.reserve_username(username)
        
        # Step 3: Request MFA email
        self.request_mfa_email(username, email, first_name, last_name, country, language)
        
        # Step 4: Get recaptcha key
        recaptcha_key = self.get_recaptcha_key()
        
        # Step 5: Get MFA code (automatically if not provided)
        if mfa_code is None and auto_retrieve_mfa:
            logger.info("MFA code not provided, retrieving automatically from email...")
            mfa_code = self.get_mfa_code_from_email(email, max_wait_seconds=60)
            
            if not mfa_code:
                raise Exception("Failed to retrieve MFA code from email")
        elif mfa_code is None:
            raise ValueError("MFA code is required. Set auto_retrieve_mfa=True or provide mfa_code")
        
        # Step 6: Create user
        user_response = self.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            country=country,
            mfa_code=mfa_code,
            phone_number=phone_number,
            zip_code=zip_code,
            language=language
        )
        
        logger.info(f"✅ Account creation completed for: {username}")
        
        return {
            "username": username,
            "email": email,
            "client_key": client_key,
            "recaptcha_key": recaptcha_key,
            "mfa_code": mfa_code,
            "user_response": user_response
        }

    @staticmethod
    def generate_username(prefix: str = "PMP") -> str:
        """
        Generate a unique username with timestamp
        
        Args:
            prefix: Username prefix
            
        Returns:
            Generated username
        """
        timestamp = int(time.time())
        return f"{prefix}{timestamp}"

    @staticmethod
    def generate_random_name() -> tuple:
        """
        Generate random first and last names
        
        Returns:
            Tuple of (first_name, last_name)
        """
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        return random.choice(first_names), random.choice(last_names)
