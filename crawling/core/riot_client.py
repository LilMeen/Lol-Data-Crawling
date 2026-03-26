import time
from typing import Any
import requests

from crawling.config.constants import BASE_URL
from crawling.core.rate_limiter import RateWindow, SimpleRateLimiter


class RiotClient:
    def __init__(self, api_key: str) -> None:
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": api_key})
        self.limiter = SimpleRateLimiter(
            windows=[RateWindow(18, 1.0), RateWindow(98, 120.0)]
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        max_retries = 3
        url = f"{BASE_URL}{path}"

        for attempt in range(1, max_retries + 1):
            self.limiter.wait_if_needed()
            response = self.session.get(url, params=params, timeout=20)
            self.limiter.record_request()

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "1")
                wait_seconds = float(retry_after) if retry_after.isdigit() else 1.0
                print(f"[429] Rate limit exceeded. Sleeping {wait_seconds:.1f}s...")
                time.sleep(wait_seconds)
                continue

            if 500 <= response.status_code < 600 and attempt < max_retries:
                backoff = 1.5 * attempt
                print(f"[{response.status_code}] Retrying after {backoff:.1f}s...")
                time.sleep(backoff)
                continue

            if response.status_code == 401:
                raise RuntimeError(
                    "Riot API returned 401 Unauthorized. "
                    "Your API key is missing/invalid/expired (dev keys expire every 24h). "
                    "Regenerate key on developer.riotgames.com, then set RIOT_API_KEY again."
                )

            response.raise_for_status()
            return response.json()

        raise RuntimeError("Failed to call Riot API after retries.")