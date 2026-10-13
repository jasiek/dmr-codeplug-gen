import time


class RateLimiter:
    """
    Paces requests to a single API and honours its rate-limit headers.

    Brandmeister doesn't document its limits. Observed behaviour (Oct 2026):
    responses carry X-RateLimit-Limit (120) and X-RateLimit-Remaining, the
    quota does not refill within a minute, and once exhausted the API returns
    429 with Retry-After and X-RateLimit-Reset (epoch seconds). Rather than
    hardcode a window, we space requests out and back off on what the
    headers tell us.
    """

    def __init__(self, min_interval=1.0, clock=time.time, sleep=time.sleep):
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last_request = None
        self._blocked_until = None

    def wait(self):
        """Block until the next request is allowed."""
        now = self._clock()
        ready_at = now
        if self._last_request is not None:
            ready_at = max(ready_at, self._last_request + self.min_interval)
        if self._blocked_until is not None:
            ready_at = max(ready_at, self._blocked_until)
        if ready_at > now:
            self._sleep(ready_at - now)
        self._last_request = self._clock()

    def update(self, response):
        """Record rate-limit headers from a response."""
        headers = response.headers
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        retry_after = headers.get("Retry-After")

        if response.status_code == 429 and retry_after:
            self._block_until(self._clock() + float(retry_after))
        elif remaining is not None and int(remaining) <= 0 and reset:
            self._block_until(float(reset))

    def _block_until(self, timestamp):
        if self._blocked_until is None or timestamp > self._blocked_until:
            self._blocked_until = timestamp
        remaining = self._blocked_until - self._clock()
        if remaining > 0:
            print(f"Rate limit reached; pausing {remaining:.0f}s")
