"""
Locator Extraction Utility
Extracts multiple selector types for each element to support self-healing framework
"""

from playwright.sync_api import sync_playwright
from config.config import config
from utilities.logger import get_logger
import json
from pathlib import Path

logger = get_logger(__name__)


class LocatorExtractor:
    """Extract multiple selector types for page elements"""
    
    def __init__(self, page):
        self.page = page
        self.extracted_locators = {}
    
    def extract_element_selectors(self, element, element_name):
        """
        Extract multiple selector types for a single element
        
        Args:
            element: Playwright element handle
            element_name: Logical name for the element
            
        Returns:
            List of selectors in priority order
        """
        selectors = []
        
        try:
            # Get element properties
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            element_id = element.evaluate("el => el.id")
            classes = element.evaluate("el => Array.from(el.classList)")
            attributes = element.evaluate("""
                el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            text = element.evaluate("el => el.textContent ? el.textContent.trim() : ''")
            
            # Priority 1: data-testid, data-test, test-id
            for attr in ['data-testid', 'data-test', 'test-id', 'data-test-id']:
                if attr in attributes and attributes[attr]:
                    selectors.append(f"[{attr}='{attributes[attr]}']")
            
            # Priority 2: aria-label
            if 'aria-label' in attributes and attributes['aria-label']:
                selectors.append(f"[aria-label='{attributes['aria-label']}']")
            
            # Priority 3: ID (if not dynamic)
            if element_id and not self._is_dynamic_id(element_id):
                selectors.append(f"#{element_id}")
            
            # Priority 4: name attribute
            if 'name' in attributes and attributes['name']:
                selectors.append(f"[name='{attributes['name']}']")
            
            # Priority 5: type + name combination for inputs
            if tag_name == 'input' and 'type' in attributes:
                input_type = attributes['type']
                if 'name' in attributes:
                    selectors.append(f"input[type='{input_type}'][name='{attributes['name']}']")
                else:
                    selectors.append(f"input[type='{input_type}']")
            
            # Priority 6: role attribute
            if 'role' in attributes and attributes['role']:
                selectors.append(f"[role='{attributes['role']}']")
            
            # Priority 7: CSS classes (if unique enough)
            if classes and len(classes) > 0:
                # Try single class first
                for cls in classes:
                    if not self._is_dynamic_class(cls):
                        class_selector = f".{cls}"
                        if self._is_unique_selector(class_selector):
                            selectors.append(class_selector)
                            break
                
                # Try class combination
                if len(classes) > 1:
                    stable_classes = [c for c in classes if not self._is_dynamic_class(c)]
                    if stable_classes:
                        class_selector = f"{tag_name}." + ".".join(stable_classes[:3])
                        selectors.append(class_selector)
            
            # Priority 8: Tag + text (for buttons, links)
            if text and tag_name in ['button', 'a', 'span', 'div']:
                # Escape quotes in text
                escaped_text = text.replace("'", "\\'")
                if len(escaped_text) < 50:  # Only for short text
                    selectors.append(f"{tag_name}:has-text('{escaped_text}')")
            
            # Priority 9: CSS selector with tag and attributes
            if 'type' in attributes and tag_name in ['input', 'button']:
                selectors.append(f"{tag_name}[type='{attributes['type']}']")
            
            return selectors[:5]  # Return top 5 selectors
            
        except Exception as e:
            logger.error(f"Failed to extract selectors for {element_name}: {str(e)}")
            return []
    
    def _is_dynamic_id(self, element_id):
        """Check if ID appears to be dynamically generated"""
        import re
        # Check for patterns like: id-12345, auto-gen-67890, uuid patterns
        return bool(re.search(r'\d{4,}|[a-f0-9]{8}-[a-f0-9]{4}', element_id.lower()))
    
    def _is_dynamic_class(self, class_name):
        """Check if class appears to be dynamically generated"""
        import re
        # Check for hash-like patterns, random strings
        return bool(re.search(r'[a-f0-9]{6,}|_\d{5,}', class_name.lower()))
    
    def _is_unique_selector(self, selector):
        """Check if selector matches exactly one element"""
        try:
            return self.page.locator(selector).count() == 1
        except:
            return False
    
    def extract_page_locators(self, page_name, element_definitions):
        """
        Extract locators for all elements on a page
        
        Args:
            page_name: Name of the page
            element_definitions: Dict of {element_name: current_selector}
            
        Returns:
            Dict of {element_name: [list of selectors]}
        """
        logger.info(f"Extracting locators for page: {page_name}")
        page_locators = {}
        
        for element_name, current_selector in element_definitions.items():
            try:
                # Try to find element with current selector
                locator = self.page.locator(current_selector).first
                
                if locator.count() > 0:
                    element_handle = locator.element_handle()
                    if element_handle:
                        selectors = self.extract_element_selectors(element_handle, element_name)
                        if selectors:
                            page_locators[element_name] = selectors
                            logger.info(f"  ✓ {element_name}: {len(selectors)} selectors found")
                        else:
                            logger.warning(f"  ✗ {element_name}: No selectors extracted")
                else:
                    logger.warning(f"  ✗ {element_name}: Element not found with selector: {current_selector}")
                    
            except Exception as e:
                logger.error(f"  ✗ {element_name}: Error - {str(e)}")
        
        return page_locators
    
    def save_to_file(self, output_path):
        """Save extracted locators to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_locators, f, indent=2)
        
        logger.info(f"Locators saved to: {output_file}")


def main():
    """Main extraction process"""
    logger.info("=" * 80)
    logger.info("LOCATOR EXTRACTION STARTED")
    logger.info("=" * 80)
    
    with sync_playwright() as playwright:
        # Launch browser
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        extractor = LocatorExtractor(page)
        
        # Navigate to login page
        base_url = config.get_base_url()
        logger.info(f"Navigating to: {base_url}")
        page.goto(base_url, wait_until="networkidle")
        page.wait_for_timeout(2000)
        
        # Extract Landing Page locators
        logger.info("\n" + "=" * 60)
        logger.info("LANDING PAGE")
        logger.info("=" * 60)
        
        landing_elements = {
            'sign_in_button': '#landing-login-button-id',
        }
        
        landing_locators = extractor.extract_page_locators('landing_page', landing_elements)
        extractor.extracted_locators['landing_page'] = landing_locators
        
        # Click sign in to reveal login form
        try:
            page.click('#landing-login-button-id')
            page.wait_for_timeout(2000)
        except:
            logger.warning("Could not click sign in button")
        
        # Extract Login Page locators
        logger.info("\n" + "=" * 60)
        logger.info("LOGIN PAGE")
        logger.info("=" * 60)
        
        login_elements = {
            'username_input': "input[type='text'], input[type='email'], input[name='username']",
            'password_input': "input[type='password']",
            'login_button': "button:has-text('Sign in')",
            'login_form': "form",
        }
        
        login_locators = extractor.extract_page_locators('carelink_login_page', login_elements)
        extractor.extracted_locators['carelink_login_page'] = login_locators
        
        # Login to access dashboard
        try:
            from config.config import Config
            cfg = Config()
            credentials = cfg.get_credentials('standard')
            
            page.fill("input[type='text'], input[type='email']", credentials['username'])
            page.wait_for_timeout(500)
            page.fill("input[type='password']", credentials['password'])
            page.wait_for_timeout(500)
            page.click("button:has-text('Sign in')")
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            
            logger.info("Successfully logged in")
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
        
        # Extract Dashboard Page locators
        logger.info("\n" + "=" * 60)
        logger.info("DASHBOARD PAGE")
        logger.info("=" * 60)
        
        dashboard_elements = {
            'dash_body': 'body',
            'dash_board': '[class*="dashboard"]',
            'dash_header': '[class*="header"]',
            'dash_nav': '[class*="nav"]',
            'dash_content': '[class*="content"]',
            'dash_main': '[class*="main"]',
        }
        
        dashboard_locators = extractor.extract_page_locators('dashboard_page', dashboard_elements)
        extractor.extracted_locators['dashboard_page'] = dashboard_locators
        
        # Extract Reports Page locators (if accessible)
        logger.info("\n" + "=" * 60)
        logger.info("REPORTS PAGE")
        logger.info("=" * 60)
        
        # Try to navigate to reports
        try:
            # Look for reports link/button
            reports_selectors = [
                'a:has-text("Reports")',
                'button:has-text("Reports")',
                '[href*="reports"]',
                '[data-testid*="reports"]',
            ]
            
            for selector in reports_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        page.wait_for_load_state("networkidle", timeout=10000)
                        page.wait_for_timeout(2000)
                        logger.info("Navigated to reports page")
                        break
                except:
                    continue
            
            reports_elements = {
                'reports_body': 'body',
                'reports_container': '[class*="reports"], [class*="report"]',
                'reports_header': 'header, [class*="header"]',
                'reports_nav': 'nav, [role="navigation"]',
                'reports_content': 'main, [role="main"], [class*="content"]',
            }
            
            reports_locators = extractor.extract_page_locators('reports_page', reports_elements)
            extractor.extracted_locators['reports_page'] = reports_locators
            
        except Exception as e:
            logger.warning(f"Could not extract reports page locators: {str(e)}")
        
        # Save results
        output_path = config.project_root / "reports" / "extracted_locators.json"
        extractor.save_to_file(output_path)
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("EXTRACTION SUMMARY")
        logger.info("=" * 80)
        for page_name, elements in extractor.extracted_locators.items():
            logger.info(f"{page_name}: {len(elements)} elements extracted")
        
        # Close browser
        browser.close()
    
    logger.info("\n" + "=" * 80)
    logger.info("LOCATOR EXTRACTION COMPLETED")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
