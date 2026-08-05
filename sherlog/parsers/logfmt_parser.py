"""Parser for logfmt (key=value) logs."""

import re

from sherlog.utils.timestamp import extract_timestamp

from .base import LogEvent

LOGFMT_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')


def parse_line(line: str, service: str = "unknown") -> LogEvent | None:
    line = line.strip()
    if not line:
        return None
    pairs = {m.group(1): m.group(2).strip('"') for m in LOGFMT_RE.finditer(line)}
    if len(pairs) < 2:
        return None

    ts_raw = pairs.get("time") or pairs.get("ts") or pairs.get("timestamp")
    timestamp = extract_timestamp(ts_raw) if ts_raw else extract_timestamp(line)

    level = (pairs.get("level") or pairs.get("lvl") or "INFO").upper()
    message = pairs.get("msg") or pairs.get("message") or line
    svc = pairs.get("service") or pairs.get("app") or service

    known = {"time", "ts", "timestamp", "level", "lvl", "msg", "message", "service", "app"}
    extra = {k: v for k, v in pairs.items() if k not in known}

    return LogEvent(
        timestamp=timestamp, level=level, message=message, service=svc, raw=line, extra=extra
    )
