from tokenlens.models import UsageEvent
from tokenlens.report import build_report, format_report


def event(**overrides):
    defaults = dict(
        tool="claude-code",
        session_id="s1",
        project="proj",
        model="model-x",
        timestamp="",
        input_tokens=0,
        cache_creation_tokens=0,
        cache_read_tokens=0,
        output_tokens=0,
    )
    defaults.update(overrides)
    return UsageEvent(**defaults)


def test_build_report_aggregates_totals_per_tool():
    events = [
        event(tool="claude-code", input_tokens=10, output_tokens=5),
        event(tool="claude-code", input_tokens=1, output_tokens=1),
        event(tool="codex-cli", input_tokens=100),
    ]
    summaries = build_report(events)

    assert set(summaries) == {"claude-code", "codex-cli"}
    assert summaries["claude-code"].events == 2
    assert summaries["claude-code"].total_tokens == 10 + 5 + 1 + 1
    assert summaries["codex-cli"].total_tokens == 100


def test_fixed_cost_only_counts_first_event_with_cache_write():
    events = [
        event(session_id="s1", is_first_in_session=True, cache_creation_tokens=1000),
        event(session_id="s1", is_first_in_session=False, cache_creation_tokens=50),
        event(session_id="s2", is_first_in_session=True, cache_creation_tokens=0),  # no fixed cost
    ]
    summaries = build_report(events)
    summary = summaries["claude-code"]

    assert summary.fixed_cost_tokens == 1000
    assert summary.session_count_with_fixed_cost == 1


def test_estimated_events_are_counted_and_labeled_in_output():
    events = [event(tool="cursor", input_tokens=1, is_estimated=True)]
    summaries = build_report(events)
    assert summaries["cursor"].estimated_events == 1

    text = format_report(summaries)
    assert "cursor" in text
    assert "ESTIMATED" in text


def test_format_report_handles_no_data():
    text = format_report({})
    assert "No local usage data found" in text


def test_by_project_and_by_session_track_totals_independently():
    events = [
        event(project="alpha", session_id="s1", input_tokens=10),
        event(project="alpha", session_id="s2", input_tokens=5),
        event(project="beta", session_id="s3", input_tokens=1),
    ]
    summaries = build_report(events)
    summary = summaries["claude-code"]

    assert summary.by_project["alpha"] == 15
    assert summary.by_project["beta"] == 1
    assert summary.by_session["s1"] == 10
    assert summary.by_session["s2"] == 5
