"""
Timestamp normalization — handles any format a log might throw at us.
"""

import re
from datetime import UTC, datetime

# Common timestamp patterns, ordered by specificity
TIMESTAMP_PATTERNS = [
    # ISO 8601 with timezone
    (
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})",
        ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"],
    ),
    # ISO 8601 no timezone
    (
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?",
        ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"],
    ),
    # Common log format: 2026-08-04 14:03:12
    (
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?",
        ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"],
    ),
    # Nginx/Apache: 04/Aug/2026:14:03:12 +0000
    (r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2} [+-]\d{4}", ["%d/%b/%Y:%H:%M:%S %z"]),
    # Syslog: Aug  4 14:03:12
    (r"\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}", ["%b %d %H:%M:%S", "%b  %d %H:%M:%S"]),
    # Unix timestamp (seconds)
    (r"\b1[5-9]\d{8}\b|\b2[0-9]\d{8}\b", None),
    # Unix timestamp ms
    (r"\b1[5-9]\d{11}\b|\b2[0-9]\d{11}\b", None),
]


def extract_timestamp(line: str) -> datetime | None:
    """Extract and normalize a timestamp from a log line."""
    for pattern, formats in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if not match:
            continue
        raw = match.group(0)

        # Unix timestamps
        if formats is None:
            try:
                ts = float(raw)
                if ts > 1e12:
                    ts /= 1000
                return datetime.fromtimestamp(ts, tz=UTC)
            except ValueError:
                continue

        for fmt in formats:
            try:
                dt = datetime.strptime(raw, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
            except ValueError:
                continue

    # Fallback: try dateutil if available
    try:
        from dateutil import parser as dateutil_parser
        from dateutil.parser import ParserError

        try:
            # grab first date-looking chunk
            date_pattern = r"\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\w{3}[-/]\d{4}"
            m = re.search(date_pattern, line)
            if m:
                dt = dateutil_parser.parse(line[max(0, m.start() - 2) : m.start() + 40], fuzzy=True)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt
        except (ParserError, ValueError):
            pass
    except ImportError:
        pass

    return None


def normalize(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
