import time
from collections import deque
from dataclasses import dataclass


@dataclass
class RateWindow:
    max_requests: int
    seconds: float


class SimpleRateLimiter:
    def __init__(self, windows: list[RateWindow]) -> None:
        self.windows = windows
        self.request_times: list[deque[float]] = [deque() for _ in windows]

    def wait_if_needed(self) -> None:
        now = time.monotonic()
        sleep_for = 0.0

        for i, window in enumerate(self.windows):
            timestamps = self.request_times[i]

            while timestamps and (now - timestamps[0]) >= window.seconds:
                timestamps.popleft()

            if len(timestamps) >= window.max_requests:
                oldest = timestamps[0]
                required_wait = window.seconds - (now - oldest)
                if required_wait > sleep_for:
                    sleep_for = required_wait

        if sleep_for > 0:
            time.sleep(sleep_for)

    def record_request(self) -> None:
        now = time.monotonic()
        for timestamps in self.request_times:
            timestamps.append(now)
