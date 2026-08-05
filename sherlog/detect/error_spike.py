"""Detect sudden spikes in error rate across time buckets."""

from datetime import datetime

SPIKE_THRESHOLD = 0.30  # error rate must cross this
BASELINE_BUCKETS = 5  # how many buckets to use for baseline
MIN_EVENTS_PER_BUCKET = 3  # ignore buckets with too few events


def detect_error_spikes(
    rates: dict[datetime, float],
) -> list[dict]:
    """
    rates: output of window.error_rate_per_bucket()
    Returns list of anomaly dicts.
    """
    anomalies = []
    timestamps = sorted(rates.keys())

    for i, ts in enumerate(timestamps):
        rate = rates[ts]
        if rate < SPIKE_THRESHOLD:
            continue

        # compute baseline from previous buckets
        baseline_window = timestamps[max(0, i - BASELINE_BUCKETS) : i]
        if not baseline_window:
            baseline = 0.0
        else:
            baseline = sum(rates[t] for t in baseline_window) / len(baseline_window)

        # spike = rate is significantly above baseline
        if rate > baseline + 0.20:
            anomalies.append(
                {
                    "type": "error_spike",
                    "timestamp": ts,
                    "severity": "CRITICAL" if rate > 0.8 else "ERROR",
                    "title": "Error spike detected",
                    "detail": (
                        f"Error rate jumped to {rate * 100:.1f}% (baseline: {baseline * 100:.1f}%)"
                    ),
                }
            )

    return anomalies
