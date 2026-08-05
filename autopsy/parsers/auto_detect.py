"""
Auto-detect the log format of a file/stream and return the right parser.
Strategy: sample first 20 non-empty lines and score each parser.
"""

import json
import re
from collections.abc import Callable

LOGFMT_RE = re.compile(r"\w+=\S+")


def detect_format(lines: list[str]) -> str:
    """Returns 'json', 'logfmt', or 'plaintext'."""
    sample = [line.strip() for line in lines if line.strip()][:20]
    json_score = logfmt_score = 0

    for line in sample:
        if line.startswith("{"):
            try:
                json.loads(line)
                json_score += 2
                continue
            except json.JSONDecodeError:
                pass
        if len(LOGFMT_RE.findall(line)) >= 3:
            logfmt_score += 1

    if json_score >= logfmt_score and json_score > 0:
        return "json"
    if logfmt_score > json_score:
        return "logfmt"
    return "plaintext"


def get_parser(fmt: str) -> Callable:
    if fmt == "json":
        from autopsy.parsers import json_parser

        return json_parser.parse_line
    if fmt == "logfmt":
        from autopsy.parsers import logfmt_parser

        return logfmt_parser.parse_line
    from autopsy.parsers import plaintext_parser

    return plaintext_parser.parse_line
