import sqlite3

from tokenlens.parsers.copilot import CopilotParser


def make_full_schema_db(path):
    con = sqlite3.connect(path)
    con.execute(
        """
        create table sessions (
            id text, model text, created_at text,
            total_input_tokens integer, total_output_tokens integer,
            total_cached_tokens integer, total_reasoning_tokens integer
        )
        """
    )
    con.execute(
        "insert into sessions values (?, ?, ?, ?, ?, ?, ?)",
        ("sess-1", "gpt-5", "2026-09-18T10:00:00Z", 100, 50, 30, 10),
    )
    con.execute(
        "insert into sessions values (?, ?, ?, ?, ?, ?, ?)",
        ("sess-empty", "gpt-5", "2026-09-18T10:00:00Z", 0, 0, 0, 0),  # excluded
    )
    con.execute("create table projects (id text, name text)")
    con.execute("insert into projects values (?, ?)", ("proj-1", "my-repo"))
    con.execute("create table workspaces (session_id text, project_id text)")
    con.execute("insert into workspaces values (?, ?)", ("sess-1", "proj-1"))
    con.commit()
    con.close()


def test_not_available_without_data_db(tmp_path):
    parser = CopilotParser(root=tmp_path)
    assert parser.is_available() is False
    assert list(parser.read_events()) == []


def test_reads_session_totals_and_project_name(tmp_path):
    make_full_schema_db(tmp_path / "data.db")
    parser = CopilotParser(root=tmp_path)
    assert parser.is_available() is True

    events = list(parser.read_events())
    assert len(events) == 1
    event = events[0]
    assert event.session_id == "sess-1"
    assert event.project == "my-repo"
    assert event.input_tokens == 100
    # reasoning is folded into output, per the documented assumption
    assert event.output_tokens == 50 + 10
    assert event.cache_read_tokens == 30

    assert parser is not None


def test_missing_required_columns_yields_nothing(tmp_path):
    con = sqlite3.connect(tmp_path / "data.db")
    con.execute("create table sessions (id text)")  # schema drift: too few columns
    con.commit()
    con.close()

    parser = CopilotParser(root=tmp_path)
    assert list(parser.read_events()) == []
