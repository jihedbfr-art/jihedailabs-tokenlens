import json
import sys

import pytest

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


def test_json_report_preserves_unclassified_tokens(monkeypatch, capsys):
    event = UsageEvent(
        tool="codex-cli", session_id="s1", project="proj", model="model-x",
        timestamp="", input_tokens=0, cache_creation_tokens=0,
        cache_read_tokens=0, output_tokens=0, unclassified_tokens=15,
    )
    monkeypatch.setattr(cli, "PARSERS", [FakeParser("codex-cli", True, [event])])
    monkeypatch.setattr(sys, "argv", ["tokenlens", "--json", "--top", "1"])

    cli.main()

    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == 1
    assert report["tools"][0]["total_tokens"] == 15
    assert report["tools"][0]["tokens"]["input"] == 0
    assert report["tools"][0]["tokens"]["unclassified"] == 15
    assert report["tools"][0]["top_projects"] == [{"name": "proj", "tokens": 15}]


def test_json_report_without_available_tool_is_valid_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "PARSERS", [FakeParser("fake-tool", False)])
    monkeypatch.setattr(sys, "argv", ["tokenlens", "--json"])

    cli.main()

    assert json.loads(capsys.readouterr().out) == {"schema_version": 1, "tools": []}


def test_negative_top_is_rejected(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tokenlens", "--top", "-1"])

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2
    assert "--top must be zero or greater" in capsys.readouterr().err
