from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class ClaudeCodeParser(ToolParser):
    """Reads ~/.claude/projects/<project>/<session>.jsonl transcripts.

    Each line is a JSON record. Usage lives on records with "type": "assistant",
    under message.usage: input_tokens, cache_creation_input_tokens,
    cache_read_input_tokens, output_tokens. Verified against real local transcripts
    on 2026-09-18.
    """

    name = "claude-code"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(os.path.expanduser("~")) / ".claude" / "projects"

    def is_available(self) -> bool:
        return self.root.is_dir()

    def read_events(self) -> Iterator[UsageEvent]:
        if not self.is_available():
            return
        for project_dir in sorted(self.root.iterdir()):
            if not project_dir.is_dir():
                continue
            for jsonl_path in sorted(project_dir.glob("*.jsonl")):
                yield from self._read_file(jsonl_path, project_dir.name)

    def _read_file(self, path: Path, project: str) -> Iterator[UsageEvent]:
        seen_session = False
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if record.get("type") != "assistant":
                        continue
                    message = record.get("message") or {}
                    usage = message.get("usage")
                    if not usage:
                        continue
                    event = UsageEvent(
                        tool=self.name,
                        session_id=record.get("sessionId", path.stem),
                        project=project,
                        model=message.get("model", "unknown"),
                        timestamp=record.get("timestamp", ""),
                        input_tokens=int(usage.get("input_tokens", 0)),
                        cache_creation_tokens=int(usage.get("cache_creation_input_tokens", 0)),
                        cache_read_tokens=int(usage.get("cache_read_input_tokens", 0)),
                        output_tokens=int(usage.get("output_tokens", 0)),
                        is_first_in_session=not seen_session,
                    )
                    seen_session = True
                    yield event
        except OSError:
            return
