"""
Script to inspect CareLink page structure
Helps identify the actual selectors needed for login
"""
from playwright.sync_api import sync_playwright
import time

def inspect_carelink():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Navigating to CareLink...")
        page.goto("https://carelink-stage1-next.minimed.eu")
        page.wait_for_load_state("networkidle")
        
        print(f"\nCurrent URL: {page.url}")
        print(f"Page Title: {page.title()}")
        
        # Check page structure
        print(f"\n=== Page Structure ===")
        print(f"Input fields: {page.locator('input').count()}")
        print(f"Buttons: {page.locator('button').count()}")
        print(f"Links: {page.locator('a').count()}")
        print(f"Forms: {page.locator('form').count()}")
        
        # Check for iframes
        frames = page.frames
        print(f"\nFrames: {len(frames)}")
        for i, frame in enumerate(frames):
            print(f"  Frame {i}: {frame.url}")
        
        # Try to get page content
        print(f"\n=== Checking for Shadow DOM ===")
        shadow_roots = page.evaluate("""() => {
            return document.querySelectorAll('*').length;
        }""")
        print(f"Total elements: {shadow_roots}")
        
        # Check for specific elements
        print(f"\n=== Looking for login elements ===")
        
        # Try to find elements by text
        login_text_elements = page.get_by_text("login", exact=False).count()
        print(f"Elements with 'login' text: {login_text_elements}")
        
        # Check for role-based selectors
        textboxes = page.get_by_role("textbox").count()
        buttons_by_role = page.get_by_role("button").count()
        print(f"Textboxes (by role): {textboxes}")
        print(f"Buttons (by role): {buttons_by_role}")
        
        # Get all button texts
        if buttons_by_role > 0:
            print(f"\n=== Button texts ===")
            for i in range(min(buttons_by_role, 10)):
                try:
                    button = page.get_by_role("button").nth(i)
                    text = button.inner_text()
                    print(f"  Button {i}: '{text}'")
                except Exception:
                    pass
        
        # Take a screenshot
        screenshot_path = "carelink_page_screenshot.png"
        page.screenshot(path=screenshot_path)
        print(f"\nScreenshot saved to: {screenshot_path}")
        
        # Wait for manual inspection
        print("\n=== Page is open for manual inspection ===")
        print("Press Ctrl+C to close...")
        try:
            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\nClosing browser...")
        
        browser.close()

if __name__ == "__main__":
    inspect_carelink()
