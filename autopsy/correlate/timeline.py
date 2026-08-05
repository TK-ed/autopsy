"""
Merge events from multiple sources into a single sorted timeline.
Events without timestamps are placed at the end.
"""
from datetime import datetime, timezone
from typing import List
from autopsy.parsers.base import LogEvent


def build_timeline(event_streams: List[List[LogEvent]]) -> List[LogEvent]:
    """Flatten and sort all events by timestamp."""
    all_events: List[LogEvent] = []
    for stream in event_streams:
        all_events.extend(stream)

    timestamped = [e for e in all_events if e.timestamp is not None]
    no_ts       = [e for e in all_events if e.timestamp is None]

    timestamped.sort(key=lambda e: e.timestamp)
    return timestamped + no_ts


def filter_window(
    events: List[LogEvent],
    from_dt: datetime = None,
    to_dt: datetime = None,
) -> List[LogEvent]:
    """Filter events to a specific time window."""
    result = events
    if from_dt:
        if from_dt.tzinfo is None:
            from_dt = from_dt.replace(tzinfo=timezone.utc)
        result = [e for e in result if e.timestamp and e.timestamp >= from_dt]
    if to_dt:
        if to_dt.tzinfo is None:
            to_dt = to_dt.replace(tzinfo=timezone.utc)
        result = [e for e in result if e.timestamp and e.timestamp <= to_dt]
    return result
