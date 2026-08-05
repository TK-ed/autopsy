"""Read log events from one or more files."""
from pathlib import Path
from typing import Iterator
from autopsy.parsers.base import LogEvent
from autopsy.parsers.auto_detect import detect_format, get_parser


def read_file(path: str, service: str = None) -> Iterator[LogEvent]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    svc = service or p.stem  # use filename as service name if not given

    with open(p, "r", errors="replace") as f:
        lines = f.readlines()

    fmt = detect_format(lines)
    parser = get_parser(fmt)

    for line in lines:
        event = parser(line, service=svc)
        if event:
            yield event
