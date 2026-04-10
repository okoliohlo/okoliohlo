"""
Helper Functions
Common utility functions used across the framework
"""

import time
import random
import string
from typing import Any, Callable
from functools import wraps
from utilities.logger import get_logger

logger = get_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator with exponential backoff

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")

            raise last_exception

        return wrapper

    return decorator


def wait_until(condition: Callable[[], bool], timeout: float = 10.0, poll_frequency: float = 0.5) -> bool:
    """
    Wait until condition is true

    Args:
        condition: Callable that returns boolean
        timeout: Maximum wait time in seconds
        poll_frequency: How often to check condition

    Returns:
        True if condition met, False if timeout
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            if condition():
                return True
        except Exception as e:
            logger.debug(f"Condition check failed: {str(e)}")

        time.sleep(poll_frequency)

    return False


def generate_random_string(length: int = 10, include_digits: bool = True) -> str:
    """
    Generate random string

    Args:
        length: String length
        include_digits: Include digits in string

    Returns:
        Random string
    """
    characters = string.ascii_letters
    if include_digits:
        characters += string.digits

    return ''.join(random.choice(characters) for _ in range(length))


def generate_random_email(domain: str = "test.com") -> str:
    """
    Generate random email address

    Args:
        domain: Email domain

    Returns:
        Random email
    """
    username = generate_random_string(8)
    return f"{username}@{domain}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def deep_merge(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def safe_execute(func: Callable, default_value: Any = None, *args, **kwargs) -> Any:
    """
    Safely execute function and return default on exception

    Args:
        func: Function to execute
        default_value: Value to return on exception
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Safe execute failed for {func.__name__}: {str(e)}")
        return default_value