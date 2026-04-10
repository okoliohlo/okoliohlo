"""
Common step definitions that can be reused across all test scenarios
Includes authentication, navigation, and other shared functionality
"""

from behave import given, when, then
from config.config import config, Config
import json
import subprocess
import os
from utilities.logger import get_logger
import allure
import sys

logger = get_logger(__name__)


# ============================================================================
# Authentication Steps
# ============================================================================

@when('I authenticate via API as "{user_type}" user')
def step_authenticate_via_api(context, user_type):
    """
    Authenticate via API using subprocess to avoid async conflicts
    
    This step:
    1. Runs authentication in a separate subprocess to avoid Playwright async conflicts
    2. Captures authentication cookies from the login flow
    3. Stores cookies and user info in the context for later use
    
    Args:
        user_type: Type of user (standard, admin, premium)
    
    Context attributes set:
        - context.auth_data: Full authentication data
        - context.auth_cookies: Dictionary of authentication cookies
        - context.username: Authenticated username
    """
    logger.info(f"Authenticating via API as {user_type} user")
    
    with allure.step(f"Authenticate via API as {user_type} user"):
        # Get current environment
        environment = getattr(context, 'environment', 'staging')
        
        logger.info(f"[API] Running authentication in subprocess...")
        logger.info(f"[API] Environment: {environment}, User: {user_type}")
        
        # Create inline script for subprocess
        auth_script = f"""import sys
import json
import os

# Add project root to path
project_root = os.getcwd()
sys.path.insert(0, project_root)

from business.api.api_helpers import get_patient_token_via_api

# Use new patient API login
auth_data = get_patient_token_via_api(user_type='{user_type}', country='GB')
print(json.dumps({{
    'cookies': auth_data['cookies'],
    'username': auth_data['username'],
    'auth_token': auth_data.get('auth_token', 'session_based'),
    'auth_code': auth_data.get('auth_code', '')
}}))
"""
        
        # Run authentication in subprocess
        result = subprocess.run(
            [sys.executable, '-c', auth_script],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.join(os.path.dirname(__file__), '..', '..')
        )
        
        if result.returncode != 0:
            logger.error(f"[API] Authentication failed: {result.stderr}")
            raise Exception(f"API authentication failed: {result.stderr[:500]}")
        
        # Parse JSON output (last line)
        try:
            output_lines = result.stdout.strip().split('\n')
            json_output = output_lines[-1]
            auth_data = json.loads(json_output)
        except Exception as e:
            logger.error(f"[API] Failed to parse auth data: {e}")
            logger.error(f"[API] Output: {result.stdout[-500:]}")
            raise
        
        # Store authentication data in context
        context.auth_data = auth_data
        context.auth_cookies = auth_data['cookies']
        context.username = auth_data['username']
        
        logger.info(f"[OK] API authentication successful for user: {context.username}")
        logger.info(f"[OK] Captured {len(context.auth_cookies)} cookies")
        
        # Attach authentication info to Allure
        allure.attach(
            f"Username: {context.username}\n"
            f"Cookies: {len(context.auth_cookies)}\n"
            f"Auth Type: {auth_data['auth_token']}",
            name="API Authentication Details",
            attachment_type=allure.attachment_type.TEXT
        )

# ============================================================================
# Environment Steps
# ============================================================================

@given('I am using the "{environment}" environment')
def step_set_environment(context, environment):
    """
    Set the environment for the test scenario
    
    Args:
        environment: Environment name (staging, qa, production, local)
    """
    # Set environment in context
    context.environment = environment
    
    # Update global config to use the specified environment
    Config.set_environment(environment)
    
    logger.info(f"Environment set to: {environment}")
    logger.info(f"Config reloaded with base_url: {config.get_base_url()}")
    
    # Log credentials being used (without password)
    creds = config.get_credentials("standard")
    if creds:
        logger.info(f"Standard user credentials loaded: {creds.get('username')}")
