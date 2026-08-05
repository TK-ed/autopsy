from .cascade import detect_cascades
from .error_spike import detect_error_spikes
from .silence import detect_silences


def run_all(events, buckets, services):
    anomalies = []
    anomalies.extend(detect_error_spikes(buckets))
    anomalies.extend(detect_silences(events, services))
    anomalies.extend(detect_cascades(events, services))
    anomalies.sort(key=lambda a: a["timestamp"])
    return anomalies
