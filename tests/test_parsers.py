"""Tests for log parsers."""
import pytest
from autopsy.parsers.json_parser     import parse_line as json_parse
from autopsy.parsers.logfmt_parser   import parse_line as logfmt_parse
from autopsy.parsers.plaintext_parser import parse_line as plain_parse
from autopsy.parsers.auto_detect     import detect_format


class TestJsonParser:
    def test_basic(self):
        line = '{"time":"2026-08-04T14:00:01Z","level":"error","msg":"DB timeout","service":"api"}'
        e = json_parse(line)
        assert e is not None
        assert e.level   == "ERROR"
        assert e.service == "api"
        assert "DB timeout" in e.message

    def test_returns_none_for_non_json(self):
        assert json_parse("this is not json") is None

    def test_fallback_service(self):
        e = json_parse('{"level":"info","msg":"hello"}', service="myapp")
        assert e.service == "myapp"

    def test_severity_field(self):
        e = json_parse('{"severity":"WARN","message":"slow query","ts":"2026-08-04T10:00:00Z"}')
        assert e.level == "WARN"


class TestLogfmtParser:
    def test_basic(self):
        line = 'ts=2026-08-04T14:00:00Z level=error msg="job failed" service=worker'
        e = logfmt_parse(line)
        assert e is not None
        assert e.level   == "ERROR"
        assert e.service == "worker"
        assert "job failed" in e.message

    def test_skips_non_logfmt(self):
        e = logfmt_parse("plain text with no key=value pairs here at all")
        assert e is None or e.level == "INFO"


class TestPlaintextParser:
    def test_error_level(self):
        line = "2026-08-04 14:03:05 ERROR upstream returned 502"
        e = plain_parse(line)
        assert e.level == "ERROR"
        assert "502" in e.message

    def test_warn_level(self):
        line = "2026-08-04 14:02:00 WARN upstream response time 850ms"
        e = plain_parse(line, service="nginx")
        assert e.level == "WARN"
        assert e.service == "nginx"

    def test_info_default(self):
        e = plain_parse("2026-08-04 14:00:00 INFO server started")
        assert e.level == "INFO"


class TestAutoDetect:
    def test_detects_json(self):
        lines = ['{"time":"2026-08-04T14:00:00Z","level":"info","msg":"ok"}\n'] * 5
        assert detect_format(lines) == "json"

    def test_detects_logfmt(self):
        lines = ["ts=2026-08-04T14:00:00Z level=info msg=ok service=api\n"] * 5
        assert detect_format(lines) == "logfmt"

    def test_detects_plaintext(self):
        lines = ["2026-08-04 14:00:00 INFO server started\n"] * 5
        assert detect_format(lines) == "plaintext"
