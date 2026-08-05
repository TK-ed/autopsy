"""Detect sudden spikes in error rate across time buckets."""
from datetime import datetime
from typing import List, Dict


SPIKE_THRESHOLD      = 0.30   # error rate must cross this
BASELINE_BUCKETS     = 5      # how many buckets to use for baseline
MIN_EVENTS_PER_BUCKET = 3     # ignore buckets with too few events


def detect_error_spikes(
    rates: Dict[datetime, float],
) -> List[dict]:
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
        baseline_window = timestamps[max(0, i - BASELINE_BUCKETS):i]
        if not baseline_window:
            baseline = 0.0
        else:
            baseline = sum(rates[t] for t in baseline_window) / len(baseline_window)

        # spike = rate is significantly above baseline
        if rate > baseline + 0.20:
            anomalies.append({
                "type":      "error_spike",
                "timestamp": ts,
                "severity":  "CRITICAL" if rate > 0.8 else "ERROR",
                "title":     f"Error spike detected",
                "detail":    (
                    f"Error rate jumped to {rate*100:.1f}% "
                    f"(baseline: {baseline*100:.1f}%)"
                ),
            })

    return anomalies
