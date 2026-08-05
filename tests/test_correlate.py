"""Tests for timeline building and windowing."""

from datetime import UTC, datetime

from sherlog.correlate.timeline import build_timeline, filter_window
from sherlog.correlate.window import bucket_events, error_rate_per_bucket
from sherlog.parsers.base import LogEvent


def make_event(ts_str, level="INFO", service="api", msg="test"):
    ts = datetime.fromisoformat(ts_str)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return LogEvent(timestamp=ts, level=level, service=service, message=msg, raw=msg)


class TestTimeline:
    def test_sorts_by_timestamp(self):
        e1 = make_event("2026-08-04T14:05:00+00:00")
        e2 = make_event("2026-08-04T14:01:00+00:00")
        e3 = make_event("2026-08-04T14:03:00+00:00")
        tl = build_timeline([[e1], [e2], [e3]])
        assert tl[0].timestamp < tl[1].timestamp < tl[2].timestamp

    def test_filter_window(self):
        events = [
            make_event("2026-08-04T13:00:00+00:00"),
            make_event("2026-08-04T14:00:00+00:00"),
            make_event("2026-08-04T15:00:00+00:00"),
        ]
        from_dt = datetime(2026, 8, 4, 13, 30, tzinfo=UTC)
        to_dt = datetime(2026, 8, 4, 14, 30, tzinfo=UTC)
        result = filter_window(events, from_dt, to_dt)
        assert len(result) == 1
        assert result[0].timestamp.hour == 14


class TestBuckets:
    def test_error_rate(self):
        events = [
            make_event("2026-08-04T14:00:10+00:00", level="ERROR"),
            make_event("2026-08-04T14:00:20+00:00", level="ERROR"),
            make_event("2026-08-04T14:00:30+00:00", level="INFO"),
            make_event("2026-08-04T14:00:40+00:00", level="INFO"),
        ]
        buckets = bucket_events(events, bucket_seconds=60)
        rates = error_rate_per_bucket(buckets)
        rate = next(iter(rates.values()))
        assert abs(rate - 0.5) < 0.01
