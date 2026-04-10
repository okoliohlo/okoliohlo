#!/usr/bin/env python
"""
Script to capture API endpoints during UI login using Playwright
This will help identify the authentication API sequence
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from config.config import Config
from utilities.logger import get_logger

logger = get_logger(__name__)


def capture_login_api_sequence(environment: str = "staging", user_type: str = "standard"):
    """
    Capture API requests during UI login
    
    Args:
        environment: Environment to test (staging, qa, etc.)
        user_type: User type for credentials (standard, admin, etc.)
    """
    # Set environment
    Config.set_environment(environment)
    config = Config()
    
    # Get credentials
    credentials = config.get_credentials(user_type)
    if not credentials:
        raise ValueError(f"No credentials found for user_type '{user_type}'")
    
    username = credentials.get("username")
    password = credentials.get("password")
    base_url = config.get_base_url()
    
    logger.info(f"Starting API capture for {environment} environment")
    logger.info(f"User: {username}")
    logger.info(f"Base URL: {base_url}")
    
    # Store captured requests
    captured_requests = []
    
    def handle_request(request):
        """Handle network requests"""
        # Only capture API requests (not static assets)
        if any(ext in request.url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', '.ico']):
            return
        
        # Capture request details
        request_data = {
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data if request.method in ["POST", "PUT", "PATCH"] else None
        }
        
        logger.info(f"[REQUEST] {request.method} {request.url}")
        captured_requests.append(request_data)
    
    def handle_response(response):
        """Handle network responses"""
        # Only log API responses
        if any(ext in response.url for ext in ['.js', '.css', '.png', '.jpg', '.svg', '.woff', '.ico']):
            return
        
        logger.info(f"[RESPONSE] {response.status} {response.url}")
        
        # Try to get response body for API calls
        try:
            if 'application/json' in response.headers.get('content-type', ''):
                body = response.json()
                
                # Find matching request
                for req in captured_requests:
                    if req['url'] == response.url and 'response' not in req:
                        req['response'] = {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'body': body
                        }
                        
                        # Check for token in response
                        if isinstance(body, dict):
                            if 'token' in body or 'access_token' in body or 'accessToken' in body:
                                logger.info(f"[TOKEN FOUND] in response from {response.url}")
                                logger.info(f"Response body keys: {list(body.keys())}")
                        break
        except Exception as e:
            logger.debug(f"Could not parse response body: {e}")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Set up network listeners
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        try:
            logger.info("=" * 80)
            logger.info("STEP 1: Opening CareLink page")
            logger.info("=" * 80)
            page.goto(base_url, wait_until='networkidle')
            page.wait_for_timeout(2000)
            
            logger.info("=" * 80)
            logger.info("STEP 2: Looking for Sign In button")
            logger.info("=" * 80)
            
            # Try to find and click sign in button
            sign_in_selectors = [
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'a:has-text("Sign In")',
                'a:has-text("Log In")',
                '[data-testid="sign-in"]',
                '[data-testid="login"]',
                'button[type="submit"]'
            ]
            
            sign_in_clicked = False
            for selector in sign_in_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"Found sign in button with selector: {selector}")
                        page.locator(selector).first.click()
                        sign_in_clicked = True
                        page.wait_for_timeout(2000)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} not found: {e}")
            
            if not sign_in_clicked:
                logger.warning("Could not find sign in button, login form might already be visible")
            
            logger.info("=" * 80)
            logger.info("STEP 3: Entering credentials")
            logger.info("=" * 80)
            
            # Try to find username field
            username_selectors = [
                'input[type="text"]',
                'input[type="email"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[id*="username"]',
                'input[id*="email"]',
                'input[placeholder*="username"]',
                'input[placeholder*="email"]'
            ]
            
            for selector in username_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"Found username field with selector: {selector}")
                        page.locator(selector).first.fill(username)
                        page.wait_for_timeout(500)
                        break
                except Exception as e:
                    logger.debug(f"Username selector {selector} failed: {e}")
            
            # Try to find password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]'
            ]
            
            for selector in password_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"Found password field with selector: {selector}")
                        page.locator(selector).first.fill(password)
                        page.wait_for_timeout(500)
                        break
                except Exception as e:
                    logger.debug(f"Password selector {selector} failed: {e}")
            
            logger.info("=" * 80)
            logger.info("STEP 4: Clicking login button")
            logger.info("=" * 80)
            
            # Try to find and click login button
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Log In")',
                'button:has-text("Sign In")',
                'button:has-text("Login")',
                'input[type="submit"]',
                '[data-testid="login-submit"]'
            ]
            
            for selector in login_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"Found login button with selector: {selector}")
                        page.locator(selector).first.click()
                        break
                except Exception as e:
                    logger.debug(f"Login button selector {selector} failed: {e}")
            
            logger.info("=" * 80)
            logger.info("STEP 5: Waiting for authentication to complete")
            logger.info("=" * 80)
            
            # Wait for navigation or network idle
            page.wait_for_timeout(5000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            logger.info("=" * 80)
            logger.info("CAPTURED API SEQUENCE")
            logger.info("=" * 80)
            
            # Print captured requests
            for idx, req in enumerate(captured_requests, 1):
                logger.info(f"\n[{idx}] {req['method']} {req['url']}")
                
                if req.get('post_data'):
                    logger.info(f"    Request Body: {req['post_data'][:200]}...")
                
                if req.get('response'):
                    resp = req['response']
                    logger.info(f"    Response Status: {resp['status']}")
                    if resp.get('body'):
                        logger.info(f"    Response Body Keys: {list(resp['body'].keys()) if isinstance(resp['body'], dict) else 'N/A'}")
            
            # Save to file
            output_file = project_root / "reports" / "captured_api_sequence.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(captured_requests, f, indent=2, default=str)
            
            logger.info(f"\n✅ API sequence saved to: {output_file}")
            
            # Keep browser open for inspection
            logger.info("\n⏸️  Browser will stay open for 10 seconds for inspection...")
            page.wait_for_timeout(10000)
            
        except Exception as e:
            logger.error(f"Error during capture: {e}", exc_info=True)
            page.screenshot(path=str(project_root / "reports" / "capture_error.png"))
            raise
        finally:
            browser.close()
    
    return captured_requests


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Capture API sequence during UI login")
    parser.add_argument("--env", default="staging", help="Environment (staging, qa, local)")
    parser.add_argument("--user", default="standard", help="User type (standard, admin)")
    
    args = parser.parse_args()
    
    try:
        captured = capture_login_api_sequence(args.env, args.user)
        print(f"\n✅ Successfully captured {len(captured)} API requests")
    except Exception as e:
        print(f"\n❌ Failed to capture API sequence: {e}")
        sys.exit(1)
