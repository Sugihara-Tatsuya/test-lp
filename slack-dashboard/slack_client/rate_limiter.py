from __future__ import annotations

import logging
import time
from functools import wraps

from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Minimum delay between calls per tier (seconds)
TIER_DELAYS = {
    2: 1.5,  # ~20 req/min
    3: 1.2,  # ~50 req/min
}

_last_call_time: dict[int, float] = {}


def rate_limited(tier: int = 3, max_retries: int = 3):
    """Decorator that enforces Slack API rate limits."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = TIER_DELAYS.get(tier, 1.2)
            for attempt in range(max_retries + 1):
                # Enforce minimum inter-call delay
                now = time.monotonic()
                last = _last_call_time.get(tier, 0)
                wait = delay - (now - last)
                if wait > 0:
                    time.sleep(wait)

                try:
                    _last_call_time[tier] = time.monotonic()
                    return func(*args, **kwargs)
                except SlackApiError as e:
                    if e.response.status_code == 429:
                        retry_after = int(e.response.headers.get("Retry-After", 5)) + 1
                        logger.warning(
                            "Rate limited (attempt %d/%d). Retrying after %ds",
                            attempt + 1,
                            max_retries,
                            retry_after,
                        )
                        if attempt < max_retries:
                            time.sleep(retry_after)
                            continue
                    raise

        return wrapper

    return decorator
