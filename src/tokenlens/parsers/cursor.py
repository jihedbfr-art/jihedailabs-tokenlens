from __future__ import annotations

import json
import os
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path

from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class CursorParser(ToolParser):
    """Reads Cursor's local state.vscdb (SQLite key-value store).

    NOT VERIFIED against a real installation — Cursor isn't installed on the
    machine this was written on. Built from public reverse-engineering reports
    (GitHub issues/tools that inspected `cursorDiskKV`), current as of
    2026-09-18, not from Cursor's own documentation (it doesn't publish this
    schema).

    HONEST LIMITATION: multiple independent projects report that the
    `tokenCount` field on chat bubbles is unreliable or unused, and that
    Cursor's real billed usage lives on their servers, not on disk. Every
    number this parser produces is therefore marked `is_estimated=True` and
    should be read as "rough shape", not as a bill.
    """

    name = "cursor"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or self._default_root()

    @staticmethod
    def _default_root() -> Path:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", ""))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "Cursor" / "User" / "globalStorage"

    def _db_path(self) -> Path:
        return self.root / "state.vscdb"

    def is_available(self) -> bool:
        return self._db_path().is_file()

    def read_events(self) -> Iterator[UsageEvent]:
        if not self.is_available():
            return
        try:
            con = sqlite3.connect(f"file:{self._db_path()}?mode=ro", uri=True)
        except sqlite3.Error:
            return
        try:
            cur = con.cursor()
            cur.execute(
                "select key, value from cursorDiskKV where key like 'bubbleId:%'"
            )
            for key, value in cur.fetchall():
                event = self._parse_bubble(key, value)
                if event:
                    yield event
        except sqlite3.Error:
            # Schema drift or a locked/corrupt file — degrade to "no data" rather
            # than crash the whole report.
            return
        finally:
            con.close()

    def _parse_bubble(self, key: str, raw_value) -> UsageEvent | None:
        try:
            data = json.loads(raw_value)
        except (TypeError, ValueError):
            return None
        token_count = data.get("tokenCount")
        if not isinstance(token_count, (int, float)) or token_count <= 0:
            return None
        parts = key.split(":")
        composer_id = parts[1] if len(parts) > 1 else "unknown"
        return UsageEvent(
            tool=self.name,
            session_id=composer_id,
            project="unknown",  # composer entries aren't linked to a workspace here
            model=data.get("modelName") or data.get("model") or "unknown",
            timestamp="",
            input_tokens=int(token_count),
            cache_creation_tokens=0,
            cache_read_tokens=0,
            output_tokens=0,
            is_estimated=True,
        )
