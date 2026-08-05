"""Read log events from stdin (e.g. kubectl logs my-pod | autopsy --stdin)."""
import sys
from typing import Iterator
from autopsy.parsers.base import LogEvent
from autopsy.parsers.auto_detect import detect_format, get_parser


def read_stdin(service: str = "stdin") -> Iterator[LogEvent]:
    lines = sys.stdin.readlines()
    fmt = detect_format(lines)
    parser = get_parser(fmt)
    for line in lines:
        event = parser(line, service=service)
        if event:
            yield event
