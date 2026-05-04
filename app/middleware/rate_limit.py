from datetime import datetime
from typing import Dict, List


class RateLimiter:
    def __init__(self):
        self.store: Dict[str, List[float]] = {}

    def check(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = datetime.utcnow().timestamp()

        if key not in self.store:
            self.store[key] = []

        self.store[key] = [t for t in self.store[key] if now - t < window_seconds]

        if len(self.store[key]) >= max_requests:
            return False

        self.store[key].append(now)
        return True


registration_limiter = RateLimiter()
magic_link_limiter = RateLimiter()
