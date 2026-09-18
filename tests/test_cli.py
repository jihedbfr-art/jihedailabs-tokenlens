import sys

from tokenlens import cli
from tokenlens.models import UsageEvent
from tokenlens.parsers.base import ToolParser


class FakeParser(ToolParser):
    def __init__(self, name, available, events=None):
        self.name = name
        self._available = available
        self._events = events or []

    def is_available(self):
        return self._available

    def read_events(self):
        yield from self._events


def test_main_reports_no_tool_found(monkeypatch, capsys):
    monkeypatch.setattr(cli, "PARSERS", [FakeParser("fake-tool", available=False)])
    monkeypatch.setattr(sys, "argv", ["tokenlens"])

    cli.main()

    out = capsys.readouterr().out
    assert "No supported tool found" in out
    assert "fake-tool" in out


def test_main_prints_report_for_available_tool(monkeypatch, capsys):
    event = UsageEvent(
        tool="fake-tool",
        session_id="s1",
        project="proj",
        model="model-x",
        timestamp="",
        input_tokens=10,
        cache_creation_tokens=0,
        cache_read_tokens=0,
        output_tokens=5,
    )
    monkeypatch.setattr(
        cli, "PARSERS", [FakeParser("fake-tool", available=True, events=[event])]
    )
    monkeypatch.setattr(sys, "argv", ["tokenlens", "--top", "1"])

    cli.main()

    out = capsys.readouterr().out
    assert "fake-tool" in out
    assert "Total tokens: 15" in out
