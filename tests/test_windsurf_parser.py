import sqlite3

from tokenlens.parsers.windsurf import WindsurfParser


def make_full_schema_db(path):
    con = sqlite3.connect(path)
    con.execute(
        "create table sessions (id text, model text, working_directory text)"
    )
    con.execute(
        "insert into sessions values (?, ?, ?)",
        ("sess-1", "claude-sonnet-5", "/home/user/some-project"),
    )
    con.execute(
        """
        create table message_nodes (
            session_id text, input_tokens integer, output_tokens integer,
            cache_read_tokens integer, cache_creation_tokens integer
        )
        """
    )
    con.execute(
        "insert into message_nodes values (?, ?, ?, ?, ?)",
        ("sess-1", 10, 20, 30, 40),
    )
    con.execute(
        "insert into message_nodes values (?, ?, ?, ?, ?)",
        ("sess-1", 0, 0, 0, 0),  # excluded: all zero
    )
    con.commit()
    con.close()


def test_not_available_without_sessions_db(tmp_path):
    parser = WindsurfParser(root=tmp_path)
    assert parser.is_available() is False
    assert list(parser.read_events()) == []


def test_reads_real_per_message_breakdown(tmp_path):
    make_full_schema_db(tmp_path / "sessions.db")
    parser = WindsurfParser(root=tmp_path)
    assert parser.is_available() is True

    events = list(parser.read_events())
    assert len(events) == 1
    event = events[0]
    assert event.project == "some-project"
    assert event.model == "claude-sonnet-5"
    assert event.input_tokens == 10
    assert event.output_tokens == 20
    assert event.cache_read_tokens == 30
    assert event.cache_creation_tokens == 40
    assert event.is_estimated is False  # real per-call metrics, not a guess


def test_schema_drift_yields_nothing_instead_of_guessing(tmp_path):
    con = sqlite3.connect(tmp_path / "sessions.db")
    # message_nodes exists but is missing the token columns this parser needs
    con.execute("create table message_nodes (session_id text)")
    con.execute("create table sessions (id text)")
    con.commit()
    con.close()

    parser = WindsurfParser(root=tmp_path)
    assert list(parser.read_events()) == []
