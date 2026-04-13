"""Simple in-memory sliding-window rate limiter for Lambda webhook."""

import time
from collections import defaultdict

_windows: dict[str, list[float]] = defaultdict(list)

WINDOW_SECONDS = 60
MAX_REQUESTS_PER_WINDOW = 30


def is_rate_limited(key: str) -> bool:
    now = time.monotonic()
    window = _windows[key]
    # Evict expired entries
    cutoff = now - WINDOW_SECONDS
    _windows[key] = [t for t in window if t > cutoff]
    if len(_windows[key]) >= MAX_REQUESTS_PER_WINDOW:
        return True
    _windows[key].append(now)
    return False
