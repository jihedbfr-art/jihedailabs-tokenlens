import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class CopilotParser(ToolParser):
    """Reads GitHub Copilot CLI's local data store (~/.copilot/data.db).

    Schema CONFIRMED against a real local file on 2026-09-18: a `sessions`
    table with real per-session totals (total_input_tokens, total_output_tokens,
    total_cached_tokens, total_reasoning_tokens, model, timestamps), and a
    `workspaces` table linking a session back to a project name via
    `workspaces.session_id` -> `projects.name`.

    HONEST LIMITATION: the `sessions` table was empty on the machine this was
    written on (Copilot CLI installed but unused), so the *values* in these
    columns have not been observed — only the column names and types, read
    directly via PRAGMA. Two assumptions follow from that gap, both stated
    here rather than hidden:
    - `total_cached_tokens` is mapped to cache-read; there's no separate
      cache-write column at the session level (unlike `workspaces`, which
      does have both `total_cache_read_tokens` and `total_cache_write_tokens`
      — a future revision could prefer that table if sessions turns out to
      undercount).
    - `total_reasoning_tokens` is added into output tokens, on the assumption
      reasoning tokens are billed as output — not confirmed for Copilot
      specifically.

    This only targets `~/.copilot/data.db` (the Copilot CLI / agent
    workspaces product). VS Code's `github.copilot-chat` extension keeps a
    separate, near-empty `session-store.db` under globalStorage that showed
    no usable usage data when inspected and is not read here.
    """

    name = "copilot"
    REQUIRED_SESSION_COLUMNS = {
        "id",
        "model",
        "created_at",
        "total_input_tokens",
        "total_output_tokens",
    }

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(os.path.expanduser("~")) / ".copilot"

    def _db_path(self) -> Path:
        return self.root / "data.db"

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
            if not self.REQUIRED_SESSION_COLUMNS.issubset(session_columns):
                return

            has_cached = "total_cached_tokens" in session_columns
            has_reasoning = "total_reasoning_tokens" in session_columns
            cached_expr = "coalesce(total_cached_tokens, 0)" if has_cached else "0"
            reasoning_expr = "coalesce(total_reasoning_tokens, 0)" if has_reasoning else "0"

            cur.execute(
                f"""
                select id, model, created_at,
                       coalesce(total_input_tokens, 0),
                       coalesce(total_output_tokens, 0) + {reasoning_expr},
                       {cached_expr}
                from sessions
                where coalesce(total_input_tokens, 0) + coalesce(total_output_tokens, 0) > 0
                """
            )
            rows = cur.fetchall()
            project_by_session = self._project_by_session(cur)
            for session_id, model, created_at, input_tokens, output_tokens, cached_tokens in rows:
                yield UsageEvent(
                    tool=self.name,
                    session_id=session_id,
                    project=project_by_session.get(session_id, "unknown"),
                    model=model or "unknown",
                    timestamp=created_at or "",
                    input_tokens=int(input_tokens),
                    cache_creation_tokens=0,
                    cache_read_tokens=int(cached_tokens),
                    output_tokens=int(output_tokens),
                    is_first_in_session=True,
                )
        except sqlite3.Error:
            return
        finally:
            con.close()

    def _project_by_session(self, cur: sqlite3.Cursor) -> dict:
        try:
            cur.execute(
                """
                select w.session_id, p.name
                from workspaces w
                join projects p on p.id = w.project_id
                where w.session_id is not null
                """
            )
            return dict(cur.fetchall())
        except sqlite3.Error:
            return {}
