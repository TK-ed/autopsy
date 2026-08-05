"""
Fallback parser for plain/unknown log formats.
Uses regex to extract timestamp + level from any line.
"""

import re

from sherlog.utils.timestamp import extract_timestamp

from .base import LogEvent

LEVEL_RE = re.compile(
    r"\b(CRITICAL|FATAL|ERROR|ERR|WARN(?:ING)?|INFO|DEBUG|TRACE|NOTICE)\b", re.IGNORECASE
)


def parse_line(line: str, service: str = "unknown") -> LogEvent | None:
    line = line.strip()
    if not line:
        return None

    timestamp = extract_timestamp(line)

    m = LEVEL_RE.search(line)
    level = m.group(1).upper() if m else "INFO"
    if level in ("FATAL",):
        level = "CRITICAL"
    if level in ("ERR",):
        level = "ERROR"
    if level == "NOTICE":
        level = "INFO"
    if level == "TRACE":
        level = "DEBUG"

    # message = everything after the level token (or the whole line)
    if m:
        message = line[m.end() :].strip(" :-|[]")
    else:
        message = line

    return LogEvent(timestamp=timestamp, level=level, message=message, service=service, raw=line)
