"""Rate limiting system for LLM providers."""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Optional

from ..config import RateLimitConfig


class RateLimiter:
    """Rate limiter that adapts to API feedback."""

    def __init__(self, config: RateLimitConfig, provider_name: str):
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
            provider_name: Name of the provider
        """
        self.config = config
        self.provider_name = provider_name
        self.request_history = defaultdict(deque)
        self.api_adaptive_limits = {}
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire permission to make request.

        Returns:
            True if request can proceed, False if rate limited
        """
        async with self._lock:
            now = time.time()

            # Check per-minute limit
            minute_key = int(now // 60)
            minute_requests = [
                req_time
                for req_time in self.request_history["minute"]
                if int(req_time // 60) == minute_key
            ]

            if len(minute_requests) >= self.config.requests_per_minute:
                wait_time = 60 - (now % 60)
                return False

            # Check per-hour limit
            hour_key = int(now // 3600)
            hour_requests = [
                req_time
                for req_time in self.request_history["hour"]
                if int(req_time // 3600) == hour_key
            ]

            if len(hour_requests) >= self.config.requests_per_hour:
                wait_time = 3600 - (now % 3600)
                return False

            # Record this request
            self.request_history["minute"].append(now)
            self.request_history["hour"].append(now)

            # Clean old requests
            self._cleanup_old_requests(now)

            return True

    def _cleanup_old_requests(self, now: float) -> None:
        """Clean up old request history.

        Args:
            now: Current timestamp
        """
        # Clean requests older than 1 minute
        minute_cutoff = now - 60
        while (
            self.request_history["minute"]
            and self.request_history["minute"][0] < minute_cutoff
        ):
            self.request_history["minute"].popleft()

        # Clean requests older than 1 hour
        hour_cutoff = now - 3600
        while (
            self.request_history["hour"]
            and self.request_history["hour"][0] < hour_cutoff
        ):
            self.request_history["hour"].popleft()

    def update_from_response(self, response_headers: Dict[str, str]) -> None:
        """Update limits based on API response headers.

        Args:
            response_headers: Response headers from API
        """
        # This would parse rate limit headers from APIs like OpenAI
        # For now, we'll keep the configured limits
        pass

    def calculate_wait_time(self) -> float:
        """Calculate required wait time based on current limits.

        Returns:
            Wait time in seconds
        """
        now = time.time()

        # Check minute limit
        minute_key = int(now // 60)
        minute_requests = [
            req_time
            for req_time in self.request_history["minute"]
            if int(req_time // 60) == minute_key
        ]

        if len(minute_requests) >= self.config.requests_per_minute:
            return 60 - (now % 60)

        # Check hour limit
        hour_key = int(now // 3600)
        hour_requests = [
            req_time
            for req_time in self.request_history["hour"]
            if int(req_time // 3600) == hour_key
        ]

        if len(hour_requests) >= self.config.requests_per_hour:
            return 3600 - (now % 3600)

        return 0.0

    async def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        wait_time = self.calculate_wait_time()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
