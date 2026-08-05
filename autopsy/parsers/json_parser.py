"""Parser for JSON-structured logs (e.g. pino, winston, structlog)."""

import json
from datetime import UTC

from autopsy.utils.timestamp import extract_timestamp

from .base import LogEvent

LEVEL_FIELDS = ["level", "severity", "lvl", "log_level"]
MSG_FIELDS = ["message", "msg", "text", "body", "event"]
TS_FIELDS = ["time", "timestamp", "ts", "@timestamp", "datetime", "date"]
SVC_FIELDS = ["service", "app", "name", "source", "logger"]


def _find(obj: dict, keys: list) -> str | None:
    for k in keys:
        if k in obj:
            return str(obj[k])
    return None


def parse_line(line: str, service: str = "unknown") -> LogEvent | None:
    line = line.strip()
    if not line or line[0] != "{":
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None

    ts_raw = _find(obj, TS_FIELDS)
    timestamp = None
    if ts_raw:
        timestamp = extract_timestamp(ts_raw)
    if timestamp and timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    level = (_find(obj, LEVEL_FIELDS) or "INFO").upper()
    message = _find(obj, MSG_FIELDS) or line
    svc = _find(obj, SVC_FIELDS) or service

    # strip known fields from extra
    known = set(LEVEL_FIELDS + MSG_FIELDS + TS_FIELDS + SVC_FIELDS)
    extra = {k: v for k, v in obj.items() if k not in known}

    return LogEvent(
        timestamp=timestamp,
        level=level,
        message=message,
        service=svc,
        raw=line,
        extra=extra,
    )
