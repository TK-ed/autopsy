"""Detect when a service suddenly stops emitting logs."""

from sherlog.parsers.base import LogEvent

SILENCE_THRESHOLD_SECONDS = 120  # 2 minutes of silence = anomaly


def detect_silences(
    events: list[LogEvent],
    services: list[str],
) -> list[dict]:
    anomalies = []

    for service in services:
        svc_events = sorted(
            [e for e in events if e.service == service and e.timestamp is not None],
            key=lambda e: e.timestamp,
        )
        if len(svc_events) < 2:
            continue

        for i in range(1, len(svc_events)):
            gap = svc_events[i].timestamp - svc_events[i - 1].timestamp
            if gap.total_seconds() > SILENCE_THRESHOLD_SECONDS:
                anomalies.append(
                    {
                        "type": "silence",
                        "timestamp": svc_events[i - 1].timestamp,
                        "severity": "WARNING",
                        "title": f"Service silence: {service}",
                        "detail": (
                            f"No logs from '{service}' for "
                            f"{int(gap.total_seconds())}s "
                            f"({svc_events[i - 1].timestamp.strftime('%H:%M:%S')} → "
                            f"{svc_events[i].timestamp.strftime('%H:%M:%S')})"
                        ),
                    }
                )

    return anomalies
