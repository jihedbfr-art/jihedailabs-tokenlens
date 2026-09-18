from dataclasses import dataclass


@dataclass(frozen=True)
class UsageEvent:
    """One billable exchange with a model, normalized across tools."""

    tool: str  # e.g. "claude-code", "codex-cli"
    session_id: str
    project: str
    model: str
    timestamp: str  # ISO 8601, as recorded by the source tool
    input_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    output_tokens: int
    is_first_in_session: bool = False  # fixed-cost proxy: system prompt + tools + skills + CLAUDE.md

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
            + self.output_tokens
        )
