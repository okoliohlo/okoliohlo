"""
Configuration Management Module
Handles environment-specific settings and parallel execution config
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class EnvironmentConfig:
    """Environment configuration dataclass"""
    name: str
    base_url: str
    api_base_url: str
    profile_url: str = "https://profile.okoliohlo.com/"
    browser: str = "chromium"
    headless: bool = True
    timeout: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    credentials: Dict[str, Any] = field(default_factory=dict)
    database: Dict[str, Any] = field(default_factory=dict)
    features: Dict[str, bool] = field(default_factory=dict)


class Config:
    """
    Main configuration class for the framework
    Singleton pattern to ensure single configuration instance
    """

    _instance: Optional['Config'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.project_root = Path(__file__).parent.parent
        self.environment = os.getenv("TEST_ENV", "qa")
        self.parallel_workers = int(os.getenv("PARALLEL_WORKERS", "4"))

        # Load configurations
        self.env_config = self._load_environment_config()
        self.test_suites = self._load_test_suites()

        # Framework settings
        self.self_healing_enabled = os.getenv("SELF_HEALING", "true").lower() == "true"
        self.ai_analysis_enabled = os.getenv("AI_ANALYSIS", "true").lower() == "true"
        self.video_recording = os.getenv("VIDEO_RECORDING", "onfailure")
        self.screenshot_on_failure = True
        self.retry_failed_tests = int(os.getenv("RETRY_COUNT", "2"))

        # Paths
        self.reports_dir = self.project_root / "reports"
        self.allure_results_dir = self.reports_dir / "allure-results"
        self.screenshots_dir = self.reports_dir / "screenshots"
        self.videos_dir = self.reports_dir / "videos"
        self.logs_dir = self.reports_dir / "logs"

        # Paths - persistent data (self-healing DB, learned selectors)
        self.data_dir = self.project_root / "ai" / "self_healing" / "data"

        # Create directories
        self._create_directories()

    def _load_environment_config(self) -> EnvironmentConfig:
        """Load environment-specific configuration"""
        config_file = self.project_root / "config" / "environments.yaml"

        with open(config_file, 'r') as f:
            configs = yaml.safe_load(f)

        env_data = configs.get(self.environment)
        if not env_data:
            raise ValueError(f"Environment '{self.environment}' not found in config")

        return EnvironmentConfig(**env_data)

    def _load_test_suites(self) -> Dict[str, Any]:
        """Load test suite definitions"""
        suites_file = self.project_root / "config" / "test_suites.yaml"

        with open(suites_file, 'r') as f:
            return yaml.safe_load(f)

    def _create_directories(self):
        """Create necessary directories"""
        for directory in [
            self.reports_dir,
            self.allure_results_dir,
            self.screenshots_dir,
            self.videos_dir,
            self.logs_dir,
            self.data_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_base_url(self) -> str:
        """Get base URL for current environment"""
        return self.env_config.base_url

    def get_api_base_url(self) -> str:
        """Get API base URL for current environment"""
        return self.env_config.api_base_url

    def get_profile_url(self) -> str:
        """Get profile page URL for current environment"""
        return self.env_config.profile_url

    def get_credentials(self, user_type: str = "standard") -> Dict[str, str]:
        """Get credentials for specified user type"""
        return self.env_config.credentials.get(user_type, {})

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration"""
        return {
            "browser_type": self.env_config.browser,
            "headless": self.env_config.headless,
            "viewport": {
                "width": self.env_config.viewport_width,
                "height": self.env_config.viewport_height
            },
            "timeout": self.env_config.timeout
        }

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.env_config.features.get(feature_name, False)

    @classmethod
    def set_environment(cls, environment: str):
        """Set the test environment (class method for BDD tests)"""
        os.environ["TEST_ENV"] = environment
        # Reset instance to reload configuration
        if cls._instance and cls._instance._initialized:
            cls._instance._initialized = False
            cls._instance.__init__()

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get current configuration as dictionary (class method for BDD tests)"""
        instance = cls()
        return {
            "base_url": instance.get_base_url(),
            "api_base_url": instance.get_api_base_url(),
            "browser": instance.env_config.browser,
            "headless": instance.env_config.headless,
            "timeout": instance.env_config.timeout,
            "credentials": instance.env_config.credentials,
        }


# Global config instance
config = Config()