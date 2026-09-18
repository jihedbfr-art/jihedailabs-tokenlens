import sqlite3

from tokenlens.parsers.codex_cli import CodexCliParser


def make_state_db(path):
    con = sqlite3.connect(path)
    con.execute(
        """
        create table threads (
            id text, cwd text, model text, updated_at integer, tokens_used integer
        )
        """
    )
    con.execute(
        "insert into threads values (?, ?, ?, ?, ?)",
        ("thread-1", "/home/user/some-project", "gpt-5", 1758000000, 12345),
    )
    con.execute(
        "insert into threads values (?, ?, ?, ?, ?)",
        ("thread-2", "/home/user/other", "gpt-5", 1758000001, 0),  # excluded: 0 tokens
    )
    con.execute(
        "insert into threads values (?, ?, ?, ?, ?)",
        ("thread-3", None, "gpt-5", None, None),  # excluded: null tokens_used
    )
    con.commit()
    con.close()


def test_not_available_without_state_db(tmp_path):
    parser = CodexCliParser(root=tmp_path)
    assert parser.is_available() is False
    assert list(parser.read_events()) == []


def test_reads_coarse_per_thread_totals(tmp_path):
    make_state_db(tmp_path / CodexCliParser.STATE_DB)
    parser = CodexCliParser(root=tmp_path)
    assert parser.is_available() is True

    events = list(parser.read_events())
    assert len(events) == 1
    event = events[0]
    assert event.tool == "codex-cli"
    assert event.session_id == "thread-1"
    assert event.project == "some-project"
    assert event.input_tokens == 12345
    # coarse totals are bucketed under input_tokens only, never invented
    assert event.cache_creation_tokens == 0
    assert event.cache_read_tokens == 0
    assert event.output_tokens == 0
    assert event.total_tokens == 12345


def test_missing_table_degrades_to_no_data(tmp_path):
    db_path = tmp_path / CodexCliParser.STATE_DB
    sqlite3.connect(db_path).close()  # valid empty db, no "threads" table
    parser = CodexCliParser(root=tmp_path)
    assert list(parser.read_events()) == []
