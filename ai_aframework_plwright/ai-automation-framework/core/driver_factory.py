"""
Driver Factory for Playwright
Manages browser instances with self-healing capabilities integrated directly
"""

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright, Locator
from typing import Optional
import threading
from config.config import config
from utilities.logger import get_logger


logger = get_logger(__name__)


class DriverFactory:
    """
    Factory class for creating and managing Playwright browser instances
    Implements thread-local storage for parallel execution
    """

    _thread_local = threading.local()
    _playwright_instance: Optional[Playwright] = None
    _lock = threading.Lock()

    @classmethod
    def initialize_playwright(cls):
        """Initialize Playwright instance (singleton)"""
        if cls._playwright_instance is None:
            with cls._lock:
                if cls._playwright_instance is None:
                    cls._playwright_instance = sync_playwright().start()
                    logger.info("Playwright instance initialized")

    @classmethod
    def get_browser(cls, browser_type: str = None) -> Browser:
        """
        Get or create browser instance for current thread

        Args:
            browser_type: Browser type (chromium, firefox, webkit)

        Returns:
            Browser instance
        """
        if not hasattr(cls._thread_local, 'browser') or cls._thread_local.browser is None:
            cls.initialize_playwright()

            browser_type = browser_type or config.get_browser_config()["browser_type"]

            logger.info(f"Creating new browser instance: {browser_type}")

            if browser_type == "chromium":
                cls._thread_local.browser = cls._playwright_instance.chromium.launch(
                    headless=config.env_config.headless,
                    args=['--start-minimized']
                )
            elif browser_type == "firefox":
                cls._thread_local.browser = cls._playwright_instance.firefox.launch(
                    headless=config.env_config.headless
                )
            elif browser_type == "webkit":
                cls._thread_local.browser = cls._playwright_instance.webkit.launch(
                    headless=config.env_config.headless
                )
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}")

        return cls._thread_local.browser

    @classmethod
    def create_context(cls, **kwargs) -> BrowserContext:
        """
        Create new browser context with configuration

        Args:
            **kwargs: Additional context options

        Returns:
            BrowserContext instance
        """
        browser = cls.get_browser()
        browser_config = config.get_browser_config()

        context_options = {
            "viewport": browser_config["viewport"],
            "ignore_https_errors": True,
            "record_video_dir": str(config.videos_dir) if config.video_recording != "off" else None,
            "record_video_size": browser_config["viewport"] if config.video_recording != "off" else None
        }

        context_options.update(kwargs)
        context = browser.new_context(**context_options)
        context.set_default_timeout(browser_config["timeout"])

        logger.info("Browser context created")
        return context

    @classmethod
    def create_page(cls, context: BrowserContext = None) -> Page:
        """
        Create new page with self-healing capabilities integrated

        Args:
            context: Browser context (creates new if None)

        Returns:
            Page instance with self-healing
        """
        if context is None:
            context = cls.create_context()

        page = context.new_page()

        # Set up console and error logging
        page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda error: logger.error(f"Page error: {error}"))

        # Add self-healing capability if enabled
        if config.self_healing_enabled:
            from ai.self_healing.healing_engine import HealingEngine
            page._healing_engine = HealingEngine(page)
            page._original_locator = page.locator
            page.locator = lambda selector, **kwargs: cls._self_healing_locator(page, selector, **kwargs)
        
        logger.info("New page created with self-healing")
        return page

    @staticmethod
    def _self_healing_locator(page: Page, selector: str, element_name: str = None, **kwargs) -> Locator:
        """
        Enhanced locator with self-healing capability
        
        Args:
            page: Playwright Page
            selector: CSS selector or XPath
            element_name: Logical name for healing
            **kwargs: Additional locator options
        
        Returns:
            Locator with self-healing
        """
        try:
            locator = page._original_locator(selector, **kwargs)
            
            # Record success if element_name provided
            if hasattr(page, '_healing_engine') and element_name:
                try:
                    locator.wait_for(state="visible", timeout=5000)
                    page._healing_engine.record_success(element_name, selector, locator)
                except:
                    pass  # Continue to healing attempt
            
            return locator
            
        except Exception as e:
            # Attempt self-healing if enabled and element_name provided
            if hasattr(page, '_healing_engine') and element_name:
                logger.info(f"Attempting self-healing for: {element_name}")
                healed_result = page._healing_engine.heal(selector, element_name)
                
                if healed_result.success:
                    logger.info(f"Self-healing successful using: {healed_result.strategy}")
                    return healed_result.locator
            
            raise e

    @classmethod
    def close_browser(cls):
        """Close browser for current thread"""
        if hasattr(cls._thread_local, 'browser') and cls._thread_local.browser:
            cls._thread_local.browser.close()
            cls._thread_local.browser = None
            logger.info("Browser closed")

    @classmethod
    def cleanup(cls):
        """Cleanup all resources"""
        cls.close_browser()

        if cls._playwright_instance:
            cls._playwright_instance.stop()
            cls._playwright_instance = None
            logger.info("Playwright instance stopped")