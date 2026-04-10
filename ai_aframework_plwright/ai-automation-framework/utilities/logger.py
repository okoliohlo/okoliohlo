"""
Logging Configuration
Centralized logging for the framework
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config.config import config


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger with specified name

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

        # File handler - detailed logs
        log_file = config.logs_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        # Error file handler - errors only
        error_log_file = config.logs_dir / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        error_handler = logging.FileHandler(error_log_file, mode='a', encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)

    return logger


# Test execution logger
test_logger = get_logger('test_execution')