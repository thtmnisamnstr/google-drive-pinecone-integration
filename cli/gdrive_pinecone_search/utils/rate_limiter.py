"""Rate limiting utilities for API calls."""

import time
import random
from typing import Callable, Any
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .exceptions import APIRateLimitError


class RateLimiter:
    """Rate limiter for API calls with exponential backoff."""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.time_window - (now - oldest_call)
            
            if wait_time > 0:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.1 * wait_time)
                time.sleep(wait_time + jitter)
        
        # Record this call
        self.calls.append(time.time())


def rate_limited(max_calls: int, time_window: int):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the time window
        time_window: Time window in seconds
    """
    limiter = RateLimiter(max_calls, time_window)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            limiter.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry function calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_delay, min=base_delay, max=60),
            retry=retry_if_exception_type((APIRateLimitError, ConnectionError))
        )
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Pre-configured rate limiters for common APIs
GOOGLE_DRIVE_RATE_LIMITER = RateLimiter(max_calls=100, time_window=100)  # 100 requests per 100 seconds
PINECONE_RATE_LIMITER = RateLimiter(max_calls=1000, time_window=60)  # 1000 requests per minute 