from __future__ import annotations

from django.conf import settings
import time
from threading import Lock
from collections import defaultdict, deque

# I used Lock to prevent multiple threads from accessing the dictionary at the same time
_lock = Lock()
_windows: dict[str, deque] = defaultdict(deque)

def is_allowed(client_ip: str) -> tuple[bool, int]:
    """
    Check whether client_ip is within the rate limit
    """
    limit = getattr(settings, "RATE_LIMIT_PER_MINUTE", 30)
    window = 60  # seconds

     # (Why I used the monotonic time instead of time.time()?-
     #  when a server is restarted, time.time() will be reset to 0 but with monotonic it won't)
    now = time.monotonic()
    cutoff = now - window

    with _lock:
        q = _windows[client_ip]

        # Remove timestamps outside the window
        while q and q[0] < cutoff:
            q.popleft()

        count = len(q)
        if count >= limit:
            return False, 0
        
        q.append(now)
        return True, limit - count - 1
    
def reset() -> None:
    """Clear all the state - used in the test only"""
    with _lock:
        _windows.clear()