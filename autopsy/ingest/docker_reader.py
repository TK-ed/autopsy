"""Read log events from a running Docker container."""

import subprocess
from collections.abc import Iterator

from autopsy.parsers.auto_detect import detect_format, get_parser
from autopsy.parsers.base import LogEvent


def read_docker(
    container: str, since: str | None = None, service: str | None = None
) -> Iterator[LogEvent]:
    """
    container: Docker container name or ID
    since:     e.g. "2h", "30m", "2026-08-04T14:00:00"
    """
    cmd = ["docker", "logs", container]
    if since:
        cmd += ["--since", since]
    cmd += ["--timestamps"]  # adds RFC3339 timestamps

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # docker logs writes to stderr by default
        raw = result.stdout + result.stderr
    except FileNotFoundError as err:
        raise RuntimeError("Docker is not installed or not in PATH") from err

    except subprocess.TimeoutExpired as err:
        raise RuntimeError(f"Timed out reading logs from container: {container}") from err

    lines = raw.splitlines(keepends=True)
    fmt = detect_format(lines)
    parser = get_parser(fmt)
    svc = service or container

    for line in lines:
        event = parser(line, service=svc)
        if event:
            yield event
