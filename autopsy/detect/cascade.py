"""
Detect cascading failures: service A starts erroring, then service B
starts erroring within a short window — suggesting A caused B.
"""
from datetime import datetime, timezone
from typing import List
from autopsy.parsers.base import LogEvent

CASCADE_WINDOW_SECONDS = 30   # B must start erroring within 30s of A
ERROR_LEVELS = {"ERROR", "CRITICAL", "FATAL"}
MIN_ERRORS   = 3              # need at least this many errors to qualify


def _first_error_time(events, service):
    svc_events = [e for e in events if e.service == service and e.level in ERROR_LEVELS and e.timestamp is not None]
    if not svc_events:
        return None
    return min(e.timestamp for e in svc_events)


def detect_cascades(
    events: List[LogEvent],
    services: List[str],
) -> List[dict]:
    anomalies = []

    # get first error time per service
    first_errors = {}
    for svc in services:
        t = _first_error_time(events, svc)
        if t:
            count = sum(1 for e in events
                        if e.service == svc and e.level in ERROR_LEVELS)
            if count >= MIN_ERRORS:
                first_errors[svc] = t

    # find pairs where B starts erroring shortly after A
    svcs_by_time = sorted(first_errors.items(), key=lambda x: x[1])
    seen = set()

    for i, (svc_a, time_a) in enumerate(svcs_by_time):
        for svc_b, time_b in svcs_by_time[i + 1:]:
            gap = (time_b - time_a).total_seconds()
            if 0 < gap <= CASCADE_WINDOW_SECONDS:
                key = (svc_a, svc_b)
                if key not in seen:
                    seen.add(key)
                    anomalies.append({
                        "type":      "cascade",
                        "timestamp": time_a,
                        "severity":  "ERROR",
                        "title":     f"Cascading failure: {svc_a} → {svc_b}",
                        "detail":    (
                            f"'{svc_b}' started erroring {gap:.0f}s after '{svc_a}' — "
                            f"possible upstream dependency failure"
                        ),
                    })

    return anomalies
