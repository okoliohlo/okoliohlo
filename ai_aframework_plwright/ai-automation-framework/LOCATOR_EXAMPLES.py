"""
Multi-Selector Locator Examples for Self-Healing Framework

This file demonstrates the exact format for defining locators with multiple
selector types to enable robust self-healing capabilities.

Format: List of selectors in priority order
- data-testid (most stable)
- aria-label (accessibility)
- ID (if not dynamic)
- name attribute
- CSS classes
- text-based selectors
"""

# ============================================================================
# EXAMPLE 1: Login Button with Multiple Selector Types
# ============================================================================

LOGIN_BUTTON_SELECTORS = [
    "[data-testid='login-btn']",        # Priority 1: data-testid attribute
    "[aria-label='Login']",             # Priority 2: aria-label for accessibility
    ".login-form button.primary",       # Priority 3: CSS class combination
]

# Usage in page object:
# self.click_element_with_fallback(LOGIN_BUTTON_SELECTORS, "login_button")


# ============================================================================
# EXAMPLE 2: Username Input with Multiple Selector Types
# ============================================================================

USERNAME_INPUT_SELECTORS = [
    "#username",                        # Priority 1: ID (if stable)
    "[data-testid='username-input']",   # Priority 2: data-testid
    "[aria-label='Username']",          # Priority 3: aria-label
    "[name='username']",                # Priority 4: name attribute
    "input[type='text'][name='username']",  # Priority 5: type + name
    "input.input",                      # Priority 6: CSS class
    "input[type='text']",               # Priority 7: type only (least specific)
]

# Usage in page object:
# self.enter_text_with_fallback(USERNAME_INPUT_SELECTORS, username, "username_input")


# ============================================================================
# EXAMPLE 3: Navigation Menu with Multiple Selector Types
# ============================================================================

NAV_MENU_SELECTORS = [
    "[data-testid='navigation']",       # Priority 1: data-testid
    "[role='navigation']",              # Priority 2: ARIA role
    "nav",                              # Priority 3: semantic HTML tag
    "[class*='nav']",                   # Priority 4: class contains 'nav'
]

# Usage in page object:
# is_visible = self.is_element_visible_with_fallback(NAV_MENU_SELECTORS, "nav_menu")


# ============================================================================
# EXAMPLE 4: Submit Button with Text-Based Selectors
# ============================================================================

SUBMIT_BUTTON_SELECTORS = [
    "[data-testid='submit-btn']",       # Priority 1: data-testid
    "[aria-label='Submit']",            # Priority 2: aria-label
    "[name='action']",                  # Priority 3: name attribute
    "button:has-text('Submit')",        # Priority 4: text content
    "button[type='submit']",            # Priority 5: type attribute
    ".form button.primary",             # Priority 6: CSS classes
]


# ============================================================================
# EXAMPLE 5: Dashboard Header with Role-Based Selectors
# ============================================================================

DASHBOARD_HEADER_SELECTORS = [
    "[data-testid='dashboard-header']", # Priority 1: data-testid
    "[role='banner']",                  # Priority 2: ARIA role
    "header",                           # Priority 3: semantic HTML
    "[class*='header']",                # Priority 4: class contains 'header'
    "h1",                               # Priority 5: heading tag
]


# ============================================================================
# REAL EXAMPLES FROM CARELINK APPLICATION
# ============================================================================

# Sign In Button (from landing page)
SIGN_IN_BUTTON = [
    "#landing-login-button-id",
    "[data-testid='login-btn']",
    "[aria-label='Sign in']",
    ".mat-legacy-primary-button",
    "button.mat-legacy-focus-indicator.form__button.mat-legacy-primary-button",
    "button:has-text('Sign in')"
]

# Username Input (from login form)
USERNAME_INPUT = [
    "#username",
    "[data-testid='username-input']",
    "[aria-label='Username']",
    "[name='username']",
    "input[type='text'][name='username']",
    "input.input",
    "input[type='text'], input[type='email']"
]

# Password Input (from login form)
PASSWORD_INPUT = [
    "#password",
    "[data-testid='password-input']",
    "[aria-label='Password']",
    "[name='password']",
    "input[type='password'][name='password']",
    "input.input",
    "input[type='password']"
]

# Login Button (submit button in form)
LOGIN_BUTTON = [
    "[data-testid='submit-btn']",
    "[aria-label='Login']",
    "[name='action']",
    "button:has-text('Sign in')",
    "button[type='submit']",
    ".login-form button.primary"
]

# Dashboard Body
DASH_BODY = [
    "[data-testid='dashboard-body']",
    "body",
    "._widget-auto-layout",
    "[class*='dashboard']"
]

# Dashboard Navigation
DASH_NAV = [
    "[data-testid='navigation']",
    "[role='navigation']",
    "nav",
    "[class*='nav']"
]

# Reports Content Area
REPORTS_CONTENT = [
    "[data-testid='reports-content']",
    "[role='main']",
    "main",
    "._widget",
    "[class*='content']"
]


# ============================================================================
# HOW TO USE IN PAGE OBJECTS
# ============================================================================

"""
class LoginPage(BasePage):
    # Define locators with multiple selectors
    USERNAME_INPUT = [
        "#username",
        "[data-testid='username-input']",
        "[aria-label='Username']",
        "[name='username']",
    ]
    USERNAME_INPUT_NAME = "username_input"
    
    def enter_username(self, username: str):
        # Use fallback method that tries all selectors
        self.enter_text_with_fallback(
            self.USERNAME_INPUT, 
            username, 
            self.USERNAME_INPUT_NAME
        )
"""


# ============================================================================
# BEST PRACTICES
# ============================================================================

"""
✅ DO:
- Use data-testid attributes (most stable)
- Include aria-label for accessibility
- Provide 3-5 alternative selectors
- Order from most stable to least stable
- Use semantic HTML roles

❌ DON'T:
- Use dynamically generated IDs
- Rely solely on CSS classes
- Use overly specific XPath
- Use position-based selectors
- Include only one selector
"""


# ============================================================================
# SELF-HEALING BEHAVIOR
# ============================================================================

"""
When element interaction fails:

1. Try first selector: [data-testid='login-btn']
   ❌ Failed (attribute removed in UI update)

2. Try second selector: [aria-label='Login']
   ✅ Success! (Element found)

3. Framework logs healing event
4. Test continues without failure
5. Team notified to update page object

Result: Test passes despite UI change
"""
