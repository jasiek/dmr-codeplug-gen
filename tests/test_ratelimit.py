from codeplug.datasources.ratelimit import RateLimiter


class FakeClock:
    def __init__(self, now=1000.0):
        self.now = now
        self.slept = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


class FakeResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


def make_limiter(min_interval=1.0):
    clock = FakeClock()
    limiter = RateLimiter(
        min_interval=min_interval, clock=clock.time, sleep=clock.sleep
    )
    return limiter, clock


def test_first_request_does_not_wait():
    limiter, clock = make_limiter()
    limiter.wait()
    assert clock.slept == []


def test_spaces_consecutive_requests():
    limiter, clock = make_limiter(min_interval=1.0)
    limiter.wait()
    clock.now += 0.25
    limiter.wait()
    assert clock.slept == [0.75]


def test_no_wait_when_interval_already_elapsed():
    limiter, clock = make_limiter(min_interval=1.0)
    limiter.wait()
    clock.now += 5
    limiter.wait()
    assert clock.slept == []


def test_429_waits_for_retry_after():
    limiter, clock = make_limiter()
    limiter.wait()
    limiter.update(FakeResponse(429, {"Retry-After": "25"}))
    limiter.wait()
    assert clock.slept == [25.0]


def test_exhausted_quota_waits_until_reset():
    limiter, clock = make_limiter()
    limiter.wait()
    limiter.update(
        FakeResponse(200, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1040"})
    )
    limiter.wait()
    assert clock.slept == [40.0]


def test_remaining_quota_does_not_block():
    limiter, clock = make_limiter()
    limiter.wait()
    clock.now += 2
    limiter.update(
        FakeResponse(200, {"X-RateLimit-Remaining": "30", "X-RateLimit-Reset": "1040"})
    )
    limiter.wait()
    assert clock.slept == []
