from abc import ABC, abstractmethod
from collections.abc import Iterator

from tokenlens.models import UsageEvent


class ToolParser(ABC):
    """One parser per AI coding tool. Must only read local files — no network calls."""

    name: str

    @abstractmethod
    def is_available(self) -> bool:
        """True if this tool's local data directory exists on this machine."""

    @abstractmethod
    def read_events(self) -> Iterator[UsageEvent]:
        """Yield normalized usage events. Must not raise on a single malformed record —
        skip it and keep going, since transcripts are append-only logs that can be
        truncated mid-write."""
