from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Iterator
from pathlib import Path

from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class WindsurfParser(ToolParser):
    """Reads the local session database of Windsurf — renamed "Devin Desktop"
    after Cognition's acquisition; the on-disk product is still commonly
    called Windsurf, which is why this parser keeps that name.

    NOT VERIFIED against a real installation — neither Windsurf nor Devin
    Desktop is installed on the machine this was written on. Path and schema
    are taken from public reports of `sessions.db` (SQLite), current as of
    2026-09-18: a `sessions` table and a `message_nodes` table carrying real
    per-message `input_tokens`, `output_tokens`, `cache_read_tokens`,
    `cache_creation_tokens` columns — unlike Cursor, these are reported as
    genuine per-call metrics, not estimates.

    Because this is unverified, the code checks every column it needs exists
    via PRAGMA before querying, and returns nothing rather than guessing if
    the schema doesn't match.
    """

    name = "windsurf"
    REQUIRED_MESSAGE_COLUMNS = {
        "session_id",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_creation_tokens",
    }

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
        return base / "devin" / "cli"

    def _db_path(self) -> Path:
        return self.root / "sessions.db"

    def is_available(self) -> bool:
        return self._db_path().is_file()

    def _table_columns(self, cur: sqlite3.Cursor, table: str) -> set[str]:
        try:
            cur.execute(f"PRAGMA table_info({table})")
            return {row[1] for row in cur.fetchall()}
        except sqlite3.Error:
            return set()

    def read_events(self) -> Iterator[UsageEvent]:
        if not self.is_available():
            return
        try:
            con = sqlite3.connect(f"file:{self._db_path()}?mode=ro", uri=True)
        except sqlite3.Error:
            return
        try:
            cur = con.cursor()
            session_columns = self._table_columns(cur, "sessions")
            message_columns = self._table_columns(cur, "message_nodes")
            if not self.REQUIRED_MESSAGE_COLUMNS.issubset(message_columns):
                # Schema doesn't match what's documented publicly — say nothing
                # rather than report numbers from columns we can't confirm.
                return

            has_model = "model" in session_columns
            has_cwd = "working_directory" in session_columns
            model_expr = "s.model" if has_model else "'unknown'"
            cwd_expr = "s.working_directory" if has_cwd else "'unknown'"

            cur.execute(
                f"""
                select
                    m.session_id,
                    {model_expr},
                    {cwd_expr},
                    m.input_tokens,
                    m.output_tokens,
                    m.cache_read_tokens,
                    m.cache_creation_tokens
                from message_nodes m
                left join sessions s on s.id = m.session_id
                where coalesce(m.input_tokens, 0) + coalesce(m.output_tokens, 0)
                      + coalesce(m.cache_read_tokens, 0) + coalesce(m.cache_creation_tokens, 0) > 0
                """
            )
            for session_id, model, cwd, input_tokens, output_tokens, cache_read, cache_write in cur.fetchall():
                yield UsageEvent(
                    tool=self.name,
                    session_id=session_id or "unknown",
                    project=os.path.basename(cwd) if cwd else "unknown",
                    model=model or "unknown",
                    timestamp="",
                    input_tokens=int(input_tokens or 0),
                    cache_creation_tokens=int(cache_write or 0),
                    cache_read_tokens=int(cache_read or 0),
                    output_tokens=int(output_tokens or 0),
                )
        except sqlite3.Error:
            return
        finally:
            con.close()
