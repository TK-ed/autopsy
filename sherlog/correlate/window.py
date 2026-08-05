"""Group events into time buckets for rate analysis."""

from collections import defaultdict
from datetime import datetime

from sherlog.parsers.base import LogEvent


def bucket_events(
    events: list[LogEvent],
    bucket_seconds: int = 60,
) -> dict[datetime, list[LogEvent]]:
    """Group events into fixed-size time buckets."""
    buckets: dict[datetime, list[LogEvent]] = defaultdict(list)
    for event in events:
        if event.timestamp is None:
            continue
        # floor to bucket boundary
        ts = event.timestamp
        floored = ts.replace(
            second=(ts.second // bucket_seconds) * bucket_seconds,
            microsecond=0,
        )
        buckets[floored].append(event)
    return dict(sorted(buckets.items()))


def error_rate_per_bucket(
    buckets: dict[datetime, list[LogEvent]],
) -> dict[datetime, float]:
    """Return error rate (0.0-1.0) per time bucket."""
    rates = {}
    error_levels = {"ERROR", "CRITICAL", "FATAL"}
    for ts, events in buckets.items():
        if not events:
            rates[ts] = 0.0
            continue
        errors = sum(1 for e in events if e.level in error_levels)
        rates[ts] = errors / len(events)
    return rates
