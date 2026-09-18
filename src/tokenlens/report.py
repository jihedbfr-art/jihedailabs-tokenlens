from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field

from tokenlens.models import UsageEvent


@dataclass
class ToolSummary:
    tool: str
    events: int = 0
    sessions: set = field(default_factory=set)
    total_tokens: int = 0
    input_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    fixed_cost_tokens: int = 0  # sum of cache_creation on first event of each session
    session_count_with_fixed_cost: int = 0
    by_project: dict = field(default_factory=lambda: defaultdict(int))
    by_model: dict = field(default_factory=lambda: defaultdict(int))
    by_session: dict = field(default_factory=lambda: defaultdict(int))


def build_report(events: Iterable[UsageEvent]) -> dict[str, ToolSummary]:
    summaries: dict[str, ToolSummary] = {}
    for event in events:
        summary = summaries.setdefault(event.tool, ToolSummary(tool=event.tool))
        summary.events += 1
        summary.sessions.add(event.session_id)
        summary.total_tokens += event.total_tokens
        summary.input_tokens += event.input_tokens
        summary.cache_creation_tokens += event.cache_creation_tokens
        summary.cache_read_tokens += event.cache_read_tokens
        summary.output_tokens += event.output_tokens
        summary.by_project[event.project] += event.total_tokens
        summary.by_model[event.model] += event.total_tokens
        summary.by_session[event.session_id] += event.total_tokens
        if event.is_first_in_session and event.cache_creation_tokens:
            summary.fixed_cost_tokens += event.cache_creation_tokens
            summary.session_count_with_fixed_cost += 1
    return summaries


def format_report(summaries: dict[str, ToolSummary], top_n: int = 5) -> str:
    if not summaries:
        return (
            "No local usage data found for any supported tool.\n"
            "Supported so far: Claude Code, Codex CLI (coarse)."
        )

    lines: list[str] = []
    for tool, summary in summaries.items():
        lines.append(f"\n=== {tool} ===")
        lines.append(f"Sessions: {len(summary.sessions)}   Events: {summary.events}")
        lines.append(f"Total tokens: {summary.total_tokens:,}")
        lines.append(
            "  input={:,}  cache_write={:,}  cache_read={:,}  output={:,}".format(
                summary.input_tokens,
                summary.cache_creation_tokens,
                summary.cache_read_tokens,
                summary.output_tokens,
            )
        )
        if summary.session_count_with_fixed_cost:
            avg_fixed = summary.fixed_cost_tokens / summary.session_count_with_fixed_cost
            pct_of_writes = (
                100 * summary.fixed_cost_tokens / summary.cache_creation_tokens
                if summary.cache_creation_tokens
                else 0.0
            )
            lines.append(
                "Fixed cost (system prompt + tools + skills + CLAUDE.md, estimated "
                "from each session's first cache write):"
            )
            lines.append(
                f"  {summary.fixed_cost_tokens:,} tokens across "
                f"{summary.session_count_with_fixed_cost} sessions "
                f"-> avg {avg_fixed:,.0f} tokens paid before the first real reply"
            )
            lines.append(
                f"  = {pct_of_writes:.1f}% of all cache-write tokens (not compared "
                f"to cache-read, which re-accrues every message and would dwarf it)"
            )

        lines.append(f"\nTop {top_n} projects by tokens:")
        for project, tokens in sorted(
            summary.by_project.items(), key=lambda kv: kv[1], reverse=True
        )[:top_n]:
            lines.append(f"  {tokens:>12,}  {project}")

        lines.append(f"\nTop {top_n} sessions by tokens:")
        for session, tokens in sorted(
            summary.by_session.items(), key=lambda kv: kv[1], reverse=True
        )[:top_n]:
            lines.append(f"  {tokens:>12,}  {session}")

        lines.append("\nBy model:")
        for model, tokens in sorted(
            summary.by_model.items(), key=lambda kv: kv[1], reverse=True
        ):
            lines.append(f"  {tokens:>12,}  {model}")

    return "\n".join(lines)
