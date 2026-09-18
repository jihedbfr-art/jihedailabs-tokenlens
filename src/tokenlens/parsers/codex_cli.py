import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class CodexCliParser(ToolParser):
    """Reads OpenAI Codex CLI's local state database (~/.codex/state_5.sqlite).

    LIMITATION (honest, not a guess): the `threads` table exposes one aggregate
    `tokens_used` integer per thread — there is no split between input, output,
    cache-read and cache-write at this level. Each thread's `rollout_path` may
    contain that detail, but its format has not been verified yet (no populated
    session was available to inspect at the time this was written — 2026-09-18).
    Until that's confirmed, this parser reports coarse per-thread totals only,
    with all tokens bucketed under input_tokens so totals stay correct and
    nothing is fabricated.
    """

    name = "codex-cli"
    STATE_DB = "state_5.sqlite"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(os.path.expanduser("~")) / ".codex"

    def is_available(self) -> bool:
        return (self.root / self.STATE_DB).is_file()

    def read_events(self) -> Iterator[UsageEvent]:
        if not self.is_available():
            return
        db_path = self.root / self.STATE_DB
        try:
            con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        except sqlite3.Error:
            return
        try:
            cur = con.cursor()
            cur.execute(
                """
                select id, cwd, model, updated_at, tokens_used
                from threads
                where tokens_used is not null and tokens_used > 0
                """
            )
            for thread_id, cwd, model, updated_at, tokens_used in cur.fetchall():
                yield UsageEvent(
                    tool=self.name,
                    session_id=thread_id,
                    project=os.path.basename(cwd) if cwd else "unknown",
                    model=model or "unknown",
                    timestamp=str(updated_at) if updated_at is not None else "",
                    input_tokens=int(tokens_used),
                    cache_creation_tokens=0,
                    cache_read_tokens=0,
                    output_tokens=0,
                    is_first_in_session=True,
                )
        except sqlite3.Error:
            return
        finally:
            con.close()
