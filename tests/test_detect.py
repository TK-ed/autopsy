"""Tests for anomaly detectors."""
import pytest
from datetime import datetime, timezone, timedelta
from autopsy.parsers.base import LogEvent
from autopsy.detect.error_spike import detect_error_spikes
from autopsy.detect.silence     import detect_silences
from autopsy.detect.cascade     import detect_cascades
from autopsy.correlate.window   import bucket_events, error_rate_per_bucket


def make_event(ts, level="INFO", service="api", msg="test"):
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return LogEvent(timestamp=ts, level=level, service=service, message=msg, raw=msg)


BASE = datetime(2026, 8, 4, 14, 0, 0, tzinfo=timezone.utc)


class TestErrorSpike:
    def test_detects_spike(self):
        # 5 clean buckets then a spike bucket
        rates = {}
        for i in range(5):
            rates[BASE + timedelta(minutes=i)] = 0.02
        rates[BASE + timedelta(minutes=5)] = 0.95
        anomalies = detect_error_spikes(rates)
        assert len(anomalies) == 1
        assert anomalies[0]["type"] == "error_spike"

    def test_no_false_positive(self):
        rates = {BASE + timedelta(minutes=i): 0.05 for i in range(10)}
        assert detect_error_spikes(rates) == []


class TestSilence:
    def test_detects_silence(self):
        events = [
            make_event(BASE,                          service="worker"),
            make_event(BASE + timedelta(minutes=5),   service="worker"),  # 5 min gap
        ]
        anomalies = detect_silences(events, ["worker"])
        assert any(a["type"] == "silence" for a in anomalies)

    def test_no_false_positive_short_gap(self):
        events = [
            make_event(BASE,                        service="api"),
            make_event(BASE + timedelta(seconds=30), service="api"),
        ]
        assert detect_silences(events, ["api"]) == []


class TestCascade:
    def test_detects_cascade(self):
        events = (
            [make_event(BASE + timedelta(seconds=i), "ERROR", "api") for i in range(5)] +
            [make_event(BASE + timedelta(seconds=15 + i), "ERROR", "worker") for i in range(5)]
        )
        anomalies = detect_cascades(events, ["api", "worker"])
        assert any(a["type"] == "cascade" for a in anomalies)
        assert any("api" in a["title"] and "worker" in a["title"] for a in anomalies)

    def test_no_cascade_for_unrelated_services(self):
        events = (
            [make_event(BASE + timedelta(seconds=i), "ERROR", "api") for i in range(5)] +
            [make_event(BASE + timedelta(minutes=10 + i), "ERROR", "worker") for i in range(5)]
        )
        anomalies = detect_cascades(events, ["api", "worker"])
        assert anomalies == []
