import json

from tokenlens.parsers.claude_code import ClaudeCodeParser


def write_session(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")


def assistant_record(session_id, usage, model="claude-sonnet-5"):
    return {
        "type": "assistant",
        "sessionId": session_id,
        "timestamp": "2026-09-18T10:00:00Z",
        "message": {"model": model, "usage": usage},
    }


def test_not_available_when_root_missing(tmp_path):
    parser = ClaudeCodeParser(root=tmp_path / "does-not-exist")
    assert parser.is_available() is False
    assert list(parser.read_events()) == []


def test_reads_usage_from_assistant_records(tmp_path):
    project_dir = tmp_path / "my-project"
    project_dir.mkdir(parents=True)
    write_session(
        project_dir / "session-a.jsonl",
        [
            {"type": "user", "sessionId": "s1"},  # no usage, must be skipped
            assistant_record(
                "s1",
                {
                    "input_tokens": 10,
                    "cache_creation_input_tokens": 100,
                    "cache_read_input_tokens": 50,
                    "output_tokens": 20,
                },
            ),
            assistant_record(
                "s1",
                {
                    "input_tokens": 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 200,
                    "output_tokens": 30,
                },
            ),
        ],
    )

    parser = ClaudeCodeParser(root=tmp_path)
    assert parser.is_available() is True
    events = list(parser.read_events())

    assert len(events) == 2
    assert events[0].project == "my-project"
    assert events[0].is_first_in_session is True
    assert events[0].total_tokens == 10 + 100 + 50 + 20
    assert events[1].is_first_in_session is False


def test_skips_malformed_lines_without_crashing(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir(parents=True)
    path = project_dir / "session.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write("not json at all\n")
        f.write(
            json.dumps(
                assistant_record(
                    "s1",
                    {
                        "input_tokens": 1,
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                        "output_tokens": 1,
                    },
                )
            )
            + "\n"
        )

    parser = ClaudeCodeParser(root=tmp_path)
    events = list(parser.read_events())
    assert len(events) == 1
