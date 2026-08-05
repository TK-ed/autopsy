"""Group events into time buckets for rate analysis."""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict
from autopsy.parsers.base import LogEvent


def bucket_events(
    events: List[LogEvent],
    bucket_seconds: int = 60,
) -> Dict[datetime, List[LogEvent]]:
    """Group events into fixed-size time buckets."""
    buckets: Dict[datetime, List[LogEvent]] = defaultdict(list)
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
    buckets: Dict[datetime, List[LogEvent]],
) -> Dict[datetime, float]:
    """Return error rate (0.0–1.0) per time bucket."""
    rates = {}
    error_levels = {"ERROR", "CRITICAL", "FATAL"}
    for ts, events in buckets.items():
        if not events:
            rates[ts] = 0.0
            continue
        errors = sum(1 for e in events if e.level in error_levels)
        rates[ts] = errors / len(events)
    return rates
