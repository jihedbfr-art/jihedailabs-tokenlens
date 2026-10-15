import argparse

from tokenlens.parsers.claude_code import ClaudeCodeParser
from tokenlens.parsers.codex_cli import CodexCliParser
from tokenlens.parsers.copilot import CopilotParser
from tokenlens.parsers.cursor import CursorParser
from tokenlens.parsers.windsurf import WindsurfParser
from tokenlens.report import build_report, format_report, format_report_json

PARSERS = [
    ClaudeCodeParser(),
    CodexCliParser(),
    CursorParser(),
    WindsurfParser(),
    CopilotParser(),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tokenlens",
        description="Local, offline report of where your AI coding assistant tokens go.",
    )
    parser.add_argument(
        "--top", type=int, default=5, help="How many top entries to show per category."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print a machine-readable JSON report."
    )
    args = parser.parse_args()
    if args.top < 0:
        parser.error("--top must be zero or greater")

    available = [p for p in PARSERS if p.is_available()]
    if not available:
        if args.json:
            print(format_report_json({}))
            return
        print("No supported tool found on this machine.")
        print("Supported so far: " + ", ".join(p.name for p in PARSERS))
        return

    events = (event for p in available for event in p.read_events())
    summaries = build_report(events)
    print(
        format_report_json(summaries, top_n=args.top)
        if args.json else format_report(summaries, top_n=args.top)
    )


if __name__ == "__main__":
    main()
