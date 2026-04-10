"""
API Helper Functions
Common API utilities and sequences
"""

from core.api_client import APIClient
from business.api.endpoints.auth_endpoint import AuthEndpoint
from business.api.endpoints.patient_endpoint import PatientEndpoint
from config.config import config
from utilities.logger import get_logger
from typing import Dict, Optional
import requests
from pathlib import Path

logger = get_logger(__name__)


def get_token_via_api(environment: str = "staging", user_type: str = "standard", playwright_page=None) -> Dict[str, str]:
    """
    Get authentication token via API sequence (CareLink-specific)
    
    CareLink uses cookie-based session authentication through SSO.
    This function automates the login flow using Playwright to capture session cookies.
    
    Captured API sequence from UI login:
    1. GET / - Load homepage and establish session
    2. SSO redirect flow (handled by browser)
    3. POST credentials to SSO provider
    4. Redirect back with auth cookies (auth_tmp_token, c_token_valid)
    5. API calls authenticated via session cookies
    
    Args:
        environment: Environment name (e.g., "staging", "qa", "local")
        user_type: User type from credentials block (e.g., "standard", "admin", "premium")
    
    Returns:
        Dictionary with authentication details:
        {
            "auth_token": "session_based",
            "cookies": {cookie_name: cookie_value},
            "username": "Authenticated username",
            "session": requests.Session object with cookies
        }
    
    Example:
        auth_data = get_token_via_api("staging")
        auth_data = get_token_via_api("staging", "admin")
        
        # Use the session for API calls
        session = auth_data['session']
        response = session.get(f"{base_url}/patient/users/me/profile")
    """
    # Set environment to load correct config
    config.set_environment(environment)
    
    # Get credentials from config for specified user type
    credentials = config.get_credentials(user_type)
    
    if not credentials:
        raise ValueError(f"No credentials found for user_type '{user_type}' in environment '{environment}'")
    
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise ValueError(f"Invalid credentials for user_type '{user_type}' in environment '{environment}'")
    
    base_url = config.get_base_url()
    
    logger.info(f"[API] Starting CareLink authentication sequence")
    logger.info(f"[API] Environment: {environment}")
    logger.info(f"[API] User: {username} (type: {user_type})")
    logger.info(f"[API] Base URL: {base_url}")
    
    # CareLink uses SSO with cookie-based authentication
    # We need to use Playwright to handle the SSO flow
    
    logger.info("[API] Using Playwright to handle SSO authentication")
    
    auth_cookies = {}
    use_existing_page = playwright_page is not None
    
    try:
        if use_existing_page:
            # Use existing Playwright page (for Behave integration)
            logger.info("[API] Using existing Playwright page")
            page = playwright_page
            context = page.context
            
            # Step 1: Navigate to the application
            logger.info(f"[API] Step 1: Loading {base_url}")
            page.goto(base_url, wait_until='networkidle')
            page.wait_for_timeout(2000)
            
            # Step 2: Click sign in button
            logger.info(f"[API] Step 2: Clicking sign in button")
            sign_in_selectors = [
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'a:has-text("Sign In")'
            ]
            
            for selector in sign_in_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.click()
                        page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue
            
            # Step 3: Enter credentials
            logger.info(f"[API] Step 3: Entering credentials for {username}")
            
            # Find and fill username
            username_selectors = ['input[type="text"]', 'input[type="email"]', 'input[name="username"]']
            for selector in username_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.locator(selector).first.fill(username)
                        break
                except Exception:
                    continue
            
            # Find and fill password
            page.locator('input[type="password"]').first.fill(password)
            
            # Step 4: Submit login
            logger.info(f"[API] Step 4: Submitting login")
            page.locator('button[type="submit"]').first.click()
            
            # Wait for navigation and authentication
            page.wait_for_load_state('networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Step 5: Extract cookies from authenticated session
            logger.info(f"[API] Step 5: Extracting authentication cookies")
            cookies = context.cookies()
            
            for cookie in cookies:
                auth_cookies[cookie['name']] = cookie['value']
                logger.info(f"[API] Cookie: {cookie['name']}")
            
            # Step 6: Verify authentication
            logger.info(f"[API] Step 6: Verifying authentication")
            current_url = page.url
            
            if 'login' not in current_url.lower():
                logger.info(f"[API] Authentication successful - redirected to: {current_url}")
            else:
                logger.warning(f"[API] Still on login page: {current_url}")
            
            # if not use_existing_page:
            #     browser.close()
        else:
            # Use new Playwright instance (standalone usage)
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                
                # Step 1: Navigate to the application
                logger.info(f"[API] Step 1: Loading {base_url}")
                page.goto(base_url, wait_until='networkidle')
                page.wait_for_timeout(2000)
                
                # Step 2: Click sign in button
                logger.info(f"[API] Step 2: Clicking sign in button")
                sign_in_selectors = [
                    'button:has-text("Sign In")',
                    'button:has-text("Log In")',
                    'a:has-text("Sign In")'
                ]
                
                for selector in sign_in_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.click()
                            page.wait_for_timeout(2000)
                            break
                    except Exception:
                        continue
                
                # Step 3: Enter credentials
                logger.info(f"[API] Step 3: Entering credentials for {username}")
                
                # Find and fill username
                username_selectors = ['input[type="text"]', 'input[type="email"]', 'input[name="username"]']
                for selector in username_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.locator(selector).first.fill(username)
                            break
                    except Exception:
                        continue
                
                # Find and fill password
                page.locator('input[type="password"]').first.fill(password)
                
                # Step 4: Submit login
                logger.info(f"[API] Step 4: Submitting login")
                page.locator('button[type="submit"]').first.click()
                
                # Wait for navigation and authentication
                page.wait_for_load_state('networkidle', timeout=30000)
                page.wait_for_timeout(3000)
                
                # Step 5: Extract cookies from authenticated session
                logger.info(f"[API] Step 5: Extracting authentication cookies")
                cookies = context.cookies()
                
                for cookie in cookies:
                    auth_cookies[cookie['name']] = cookie['value']
                    logger.info(f"[API] Cookie: {cookie['name']}")
                
                # Step 6: Verify authentication
                logger.info(f"[API] Step 6: Verifying authentication")
                current_url = page.url
                
                if 'login' not in current_url.lower():
                    logger.info(f"[API] Authentication successful - redirected to: {current_url}")
                else:
                    logger.warning(f"[API] Still on login page: {current_url}")
                
                browser.close()
        
        # Create requests session with captured cookies
        session = requests.Session()
        domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        for cookie in cookies:
            session.cookies.set(
                name=cookie['name'],
                value=cookie['value'],
                domain=cookie.get('domain', domain),
                path=cookie.get('path', '/'),
                secure=cookie.get('secure', True)
            )
        
        # Verify session works by calling API
        logger.info(f"[API] Step 7: Testing session with API call")
        profile_url = f"{base_url}/patient/users/me/profile"
        profile_response = session.get(profile_url, headers={"Accept": "application/json"}, timeout=30)
        
        logger.info(f"[API] Profile API response: {profile_response.status_code}")
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            logger.info(f"[API] Verified user: {profile_data.get('username', username)}")
        
        # Return authentication data
        auth_data = {
            "auth_token": "session_based",
            "cookies": auth_cookies,
            "username": username,
            "session": session
        }
        
        logger.info("[API] Authentication sequence completed successfully")
        return auth_data
        
    except Exception as e:
        logger.error(f"[API] Authentication failed: {str(e)}")
        raise


def get_patient_token_via_api(
    username: Optional[str] = None,
    password: Optional[str] = None,
    country: str = "GB",
    user_type: str = "standard",
    save_token: bool = False,
    token_file: Optional[str] = None
) -> Dict[str, any]:
    """
    Get patient authentication token via pure API sequence
    
    This function uses the patient API endpoints to:
    1. Initiate SSO login
    2. Store session cookies
    3. Optionally save token to file for reuse
    
    Args:
        username: Patient username (if None, uses config)
        password: Patient password (if None, uses config)
        country: Country code (default: GB)
        user_type: User type from config (default: standard)
        save_token: Whether to save token to file (default: False)
        token_file: Path to save token file (default: tokens/patient_session.json)
    
    Returns:
        Dictionary with authentication details:
        {
            "auth_token": "token_value",
            "cookies": {cookie_name: cookie_value},
            "username": "username",
            "client_key": "client_key_if_available",
            "authorize_url": "sso_authorize_url",
            "patient_endpoint": PatientEndpoint instance
        }
    
    Example:
        # Use credentials from config
        auth_data = get_patient_token_via_api()
        
        # Use specific credentials
        auth_data = get_patient_token_via_api(
            username="PMP1234567890",
            password="PostmanUser2023!",
            country="GB"
        )
        
        # Save token for reuse
        auth_data = get_patient_token_via_api(
            save_token=True,
            token_file="tokens/my_session.json"
        )
        
        # Use the patient_endpoint for further API calls
        patient_endpoint = auth_data['patient_endpoint']
        token = patient_endpoint.get_auth_token()
    """
    # Get credentials from config if not provided
    if not username or not password:
        credentials = config.get_credentials(user_type)
        if not credentials:
            raise ValueError(f"No credentials found for user_type '{user_type}'")
        
        username = username or credentials.get("username")
        password = password or credentials.get("password")
    
    if not username or not password:
        raise ValueError("Username and password are required")
    
    base_url = config.get_base_url()
    
    logger.info(f"[Patient API] Starting patient authentication sequence")
    logger.info(f"[Patient API] User: {username}")
    logger.info(f"[Patient API] Country: {country}")
    logger.info(f"[Patient API] Base URL: {base_url}")
    
    try:
        # Initialize API client and patient endpoint
        api_client = APIClient(base_url=base_url)
        patient_endpoint = PatientEndpoint(api_client)
        
        # Execute complete OAuth login flow
        logger.info(f"[Patient API] Executing complete OAuth login flow")
        oauth_result = patient_endpoint.complete_oauth_login_flow(
            username=username,
            password=password,
            country=country
        )
        
        # Extract results
        auth_token = oauth_result.get('auth_token')
        cookies = oauth_result.get('cookies', {})
        auth_code = oauth_result.get('auth_code')
        client_key = patient_endpoint.client_key
        
        logger.info(f"[Patient API] OAuth flow completed")
        logger.info(f"[Patient API] Captured {len(cookies)} cookies")
        
        for cookie_name in cookies.keys():
            logger.info(f"[Patient API] Cookie: {cookie_name}")
        
        # Step 4: Save token if requested
        if save_token:
            if not token_file:
                token_file = str(config.project_root / "tokens" / "patient_session.json")
            
            logger.info(f"[Patient API] Step 3: Saving token to file")
            patient_endpoint.save_token_to_file(token_file)
            logger.info(f"[Patient API] Token saved to: {token_file}")
        
        # Prepare return data
        auth_data = {
            "auth_token": auth_token,
            "cookies": cookies,
            "username": username,
            "client_key": client_key,
            "auth_code": auth_code,
            "patient_endpoint": patient_endpoint,
            "country": country
        }
        
        logger.info("[Patient API] Authentication sequence completed successfully")
        logger.info(f"[Patient API] Auth token: {'Available' if auth_token else 'Not yet available (requires OAuth completion)'}")
        
        # Print detailed token information
        logger.info("=" * 80)
        logger.info("TOKEN DETAILS:")
        logger.info("=" * 80)
        logger.info(f"Username: {username}")
        logger.info(f"Country: {country}")
        logger.info(f"Auth Token: {auth_token[:50] if auth_token else 'None'}...")
        logger.info(f"Auth Code: {auth_code[:20] if auth_code else 'None'}...")
        logger.info(f"Client Key: {client_key or 'None'}")
        logger.info(f"Cookies ({len(cookies)}):")
        for cookie_name, cookie_value in cookies.items():
            logger.info(f"  - {cookie_name}: {cookie_value[:50]}..." if len(str(cookie_value)) > 50 else f"  - {cookie_name}: {cookie_value}")
        logger.info("=" * 80)
        
        return auth_data
        
    except Exception as e:
        logger.error(f"[Patient API] Authentication failed: {str(e)}")
        raise


def load_patient_token_from_file(token_file: Optional[str] = None) -> Dict[str, any]:
    """
    Load patient authentication token from file
    
    Args:
        token_file: Path to token file (default: tokens/patient_session.json)
    
    Returns:
        Dictionary with authentication details:
        {
            "auth_token": "token_value",
            "cookies": {cookie_name: cookie_value},
            "client_key": "client_key",
            "patient_endpoint": PatientEndpoint instance
        }
    
    Example:
        # Load saved session
        auth_data = load_patient_token_from_file()
        
        # Use the patient endpoint
        patient_endpoint = auth_data['patient_endpoint']
        token = patient_endpoint.get_auth_token()
    """
    if not token_file:
        token_file = str(config.project_root / "tokens" / "patient_session.json")
    
    logger.info(f"[Patient API] Loading token from file: {token_file}")
    
    if not Path(token_file).exists():
        raise FileNotFoundError(f"Token file not found: {token_file}")
    
    try:
        # Initialize API client and patient endpoint
        base_url = config.get_base_url()
        api_client = APIClient(base_url=base_url)
        patient_endpoint = PatientEndpoint(api_client)
        
        # Load token from file
        success = patient_endpoint.load_token_from_file(token_file)
        
        if not success:
            raise Exception("Failed to load token from file")
        
        # Get loaded data
        auth_token = patient_endpoint.get_auth_token()
        cookies = patient_endpoint.get_session_cookies()
        client_key = patient_endpoint.client_key
        
        logger.info(f"[Patient API] Token loaded successfully")
        logger.info(f"[Patient API] Auth token: {'Available' if auth_token else 'Not available'}")
        logger.info(f"[Patient API] Cookies: {len(cookies)} loaded")
        
        auth_data = {
            "auth_token": auth_token,
            "cookies": cookies,
            "client_key": client_key,
            "patient_endpoint": patient_endpoint
        }
        
        return auth_data
        
    except Exception as e:
        logger.error(f"[Patient API] Failed to load token: {str(e)}")
        raise


def create_patient_account_via_api(
    username: Optional[str] = None,
    password: str = "PostmanUser2023!",
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    country: str = "GB",
    mfa_code: Optional[str] = None,
    email: Optional[str] = None,
    zip_code: Optional[str] = None
) -> Dict[str, any]:
    """
    Create new patient account via API
    
    Args:
        username: Username (auto-generated if None)
        password: Password (default: PostmanUser2023!)
        first_name: First name (auto-generated if None)
        last_name: Last name (auto-generated if None)
        country: Country code (default: GB)
        mfa_code: MFA verification code (required for completion)
        email: Email address (auto-generated if None)
        zip_code: Zip/postal code
    
    Returns:
        Dictionary with account creation details
    
    Example:
        # Create account (requires MFA code)
        account_data = create_patient_account_via_api(
            mfa_code="123456"
        )
        
        # Create account with specific details
        account_data = create_patient_account_via_api(
            username="TestUser123",
            first_name="John",
            last_name="Doe",
            country="US",
            mfa_code="123456"
        )
    """
    base_url = config.get_base_url()
    
    logger.info(f"[Patient API] Starting account creation sequence")
    
    try:
        # Initialize API client and patient endpoint
        api_client = APIClient(base_url=base_url)
        patient_endpoint = PatientEndpoint(api_client)
        
        # Generate username if not provided
        if not username:
            username = patient_endpoint.generate_username()
            logger.info(f"[Patient API] Generated username: {username}")
        
        # Generate names if not provided
        if not first_name or not last_name:
            gen_first, gen_last = patient_endpoint.generate_random_name()
            first_name = first_name or gen_first
            last_name = last_name or gen_last
            logger.info(f"[Patient API] Generated name: {first_name} {last_name}")
        
        # Generate email if not provided
        if not email:
            email = f"{username}@carelink.testinator.com"
        
        # Set default zip code for GB
        if not zip_code and country == "GB":
            zip_code = "HP5 4UX"
        
        if not mfa_code:
            logger.warning("[Patient API] MFA code not provided - account creation will be incomplete")
            logger.warning("[Patient API] Will execute steps up to MFA code requirement")
        
        # Execute account creation flow
        if mfa_code:
            logger.info(f"[Patient API] Creating account with full flow")
            result = patient_endpoint.create_account_full_flow(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                country=country,
                mfa_code=mfa_code,
                email=email,
                zip_code=zip_code
            )
        else:
            # Execute partial flow without user creation
            logger.info(f"[Patient API] Executing partial flow (no MFA code)")
            
            # Get consents
            consents = patient_endpoint.get_consents(country=country)
            logger.info(f"[Patient API] Retrieved {len(consents)} consents")
            
            # Reserve username
            client_key = patient_endpoint.reserve_username(username)
            logger.info(f"[Patient API] Username reserved: {client_key}")
            
            # Request MFA email
            patient_endpoint.request_mfa_email(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                country=country
            )
            logger.info(f"[Patient API] MFA email sent to: {email}")
            
            # Get recaptcha key
            recaptcha_key = patient_endpoint.get_recaptcha_key()
            logger.info(f"[Patient API] Recaptcha key obtained")
            
            result = {
                "username": username,
                "email": email,
                "client_key": client_key,
                "recaptcha_key": recaptcha_key,
                "status": "pending_mfa",
                "message": "Account creation pending - MFA code required"
            }
        
        logger.info("[Patient API] Account creation sequence completed")
        return result
        
    except Exception as e:
        logger.error(f"[Patient API] Account creation failed: {str(e)}")
        raise
