"""Read log events from one or more files."""

from collections.abc import Iterator
from pathlib import Path

from autopsy.parsers.auto_detect import detect_format, get_parser
from autopsy.parsers.base import LogEvent


def read_file(path: str, service: str | None = None) -> Iterator[LogEvent]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    svc = service or p.stem  # use filename as service name if not given

    with open(p, errors="replace") as f:
        lines = f.readlines()

    fmt = detect_format(lines)
    parser = get_parser(fmt)

    for line in lines:
        event = parser(line, service=svc)
        if event:
            yield event
