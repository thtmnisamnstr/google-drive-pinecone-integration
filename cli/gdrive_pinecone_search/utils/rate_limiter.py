"""Rate limiting utilities for API calls."""

import time
import random
from typing import Callable, Any
from functools import wraps
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
except ModuleNotFoundError:  # pragma: no cover - tenacity required by requirements
    retry = stop_after_attempt = wait_exponential = retry_if_exception_type = None  # type: ignore

from .exceptions import APIRateLimitError, DocumentProcessingError, ConnectionError


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


def with_retry(max_attempts: int = 5, base_wait: float = 1.0):
    """Decorator to add exponential backoff retry semantics to API calls."""

    if None in (retry, stop_after_attempt, wait_exponential, retry_if_exception_type):
        raise RuntimeError("Tenacity is required for retry support but is not installed.")

    retryable = (APIRateLimitError, ConnectionError, DocumentProcessingError)

    def decorator(func: Callable) -> Callable:
        wrapped = retry(  # type: ignore[misc]
            reraise=True,
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=base_wait, max=base_wait * 16),
            retry=retry_if_exception_type(retryable),
        )(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)

        return wrapper

    return decorator

