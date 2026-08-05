"""Base log event dataclass and abstract parser."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEvent:
    timestamp: datetime | None
    level: str
    message: str
    service: str
    raw: str
    extra: dict = field(default_factory=dict)

    def __lt__(self, other):
        if self.timestamp is None:
            return True
        if other.timestamp is None:
            return False
        return self.timestamp < other.timestamp
