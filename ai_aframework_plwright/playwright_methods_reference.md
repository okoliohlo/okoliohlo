# Playwright Driver Methods Reference

## Page Object Methods

### **Navigation Methods**
```python
page.goto(url)                    # Navigate to URL
page.reload()                     # Reload current page
page.go_back()                    # Go back in history
page.go_forward()                 # Go forward in history
page.wait_for_url(url, timeout)  # Wait for URL change
```

### **Element Interaction**
```python
page.click(selector)              # Click element
page.dblclick(selector)           # Double click
page.right_click(selector)        # Right click
page.hover(selector)              # Hover over element
page.fill(selector, value)        # Fill input field
page.type(selector, text)         # Type text (slower)
page.focus(selector)              # Focus element
page.blur(selector)               # Remove focus
page.select_option(selector, value) # Select dropdown option
page.check(selector)              # Check checkbox
page.uncheck(selector)            # Uncheck checkbox
```

### **Keyboard & Mouse**
```python
page.keyboard.press(key)          # Press key (Enter, Tab, etc.)
page.keyboard.type(text)          # Type text
page.keyboard.down(key)           # Key down
page.keyboard.up(key)             # Key up

page.mouse.click(x, y)            # Click at coordinates
page.mouse.dblclick(x, y)         # Double click at coordinates
page.mouse.move(x, y)             # Move mouse to position
page.mouse.down()                  # Mouse down
page.mouse.up()                    # Mouse up
page.mouse.wheel(delta_x, delta_y) # Scroll wheel
```

### **Scrolling Methods**
```python
page.mouse.wheel(0, 1000)         # Scroll down 1000px
page.mouse.wheel(0, -1000)        # Scroll up 1000px
page.mouse.wheel(1000, 0)         # Scroll right 1000px
page.mouse.wheel(-1000, 0)        # Scroll left 1000px

page.evaluate("window.scrollBy(0, 1000)")  # JavaScript scroll
page.evaluate("window.scrollTo(0, 1000)")  # JavaScript scroll to
```

### **Waiting & Timeouts**
```python
page.wait_for_timeout(ms)         # Wait for specified milliseconds
page.wait_for_load_state(state)   # Wait for load state
page.wait_for_selector(selector)   # Wait for element to appear
page.wait_for_event(event)         # Wait for specific event
```

### **Information & Properties**
```python
page.url                          # Get current URL
page.title                        # Get page title
page.content                      # Get page HTML
page.viewport_size                # Get viewport dimensions
page.is_visible(selector)         # Check if element is visible
page.is_enabled(selector)         # Check if element is enabled
page.is_checked(selector)         # Check if checkbox is checked
```

### **Screenshots & Recording**
```python
page.screenshot()                 # Take screenshot
page.screenshot(path="file.png")   # Save screenshot to file
page.screenshot(full_page=True)    # Full page screenshot
```

### **JavaScript Execution**
```python
page.evaluate(script)             # Execute JavaScript
page.evaluate_handle(script)      # Execute and return handle
page.eval_on_selector(selector, script)  # Execute on element
```

### **Dialogs & Alerts**
```python
page.on("dialog", lambda dialog: dialog.accept())  # Handle dialogs
page.on("console", lambda msg: print(msg.text))    # Console logs
page.on("pageerror", lambda error: print(error))   # Page errors
```

### **Frame Handling**
```python
page.frame(name)                  # Get frame by name
page.frame_selector(selector)     # Get frame by selector
page.main_frame                   # Get main frame
```

### **Browser Context**
```python
page.context                      # Get browser context
page.set_viewport_size(width, height)  # Set viewport
page.bring_to_front()             # Bring page to front
page.close()                      # Close page
```

## Locator Methods (Modern Approach)

### **Element Locators**
```python
page.locator(selector)            # Create locator
page.get_by_text(text)            # Find by text content
page.get_by_role(role)            # Find by ARIA role
page.get_by_label(text)           # Find by label text
page.get_by_placeholder(text)     # Find by placeholder
page.get_by_alt_text(text)        # Find by alt text
page.get_by_title(text)           # Find by title attribute
```

### **Locator Actions**
```python
locator.click()                   # Click element
locator.fill(value)               # Fill input
locator.select_option(value)      # Select option
locator.check()                   # Check checkbox
locator.uncheck()                 # Uncheck checkbox
locator.hover()                   # Hover element
locator.focus()                   # Focus element
locator.press(key)                # Press key
locator.type(text)                # Type text
```

### **Locator Information**
```python
locator.count()                   # Count matching elements
locator.first                     # Get first matching element
locator.last                      # Get last matching element
locator.nth(index)                # Get element by index
locator.is_visible()              # Check visibility
locator.is_enabled()              # Check if enabled
locator.is_disabled()             # Check if disabled
locator.get_attribute(name)       # Get attribute value
locator.inner_text()              # Get inner text
locator.text_content()            # Get text content
locator.input_value()             # Get input value
```

### **Locator Waiting**
```python
locator.wait_for()                # Wait for element
locator.wait_for_state(state)     # Wait for specific state
locator.wait_for_element()         # Wait for element to appear
```

## Browser Methods

### **Browser Control**
```python
browser.new_page()                # Create new page
browser.new_context()             # Create new context
browser.close()                    # Close browser
browser.version()                  # Get browser version
browser.user_agent()               # Get user agent
```

## Context Methods

### **Context Management**
```python
context.new_page()                # Create page in context
context.pages()                    # Get all pages in context
context.add_cookies(cookies)       # Add cookies
context.clear_cookies()            # Clear cookies
context.set_extra_http_headers(headers)  # Set headers
context.set_geolocation(geolocation)     # Set location
context.grant_permissions(permissions)  # Grant permissions
context.close()                    # Close context
```

## Common Usage Patterns

### **Basic Navigation**
```python
page.goto("https://example.com")
page.wait_for_load_state("networkidle")
```

### **Element Interaction**
```python
page.click("button#submit")
page.fill("input[name='email']", "user@example.com")
page.select_option("select#country", "US")
```

### **Scrolling**
```python
page.mouse.wheel(0, 1000)          # Scroll down
page.evaluate("window.scrollBy(0, 500)")  # JavaScript scroll
```

### **Waiting**
```python
page.wait_for_selector(".loaded")
page.wait_for_timeout(2000)
```

### **Screenshots**
```python
page.screenshot(path="screenshot.png", full_page=True)
```

### **Error Handling**
```python
try:
    page.click("button")
except Exception as e:
    print(f"Click failed: {e}")
```
