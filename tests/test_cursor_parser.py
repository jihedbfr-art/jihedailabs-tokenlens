import json
import sqlite3

from tokenlens.parsers.cursor import CursorParser


def make_state_vscdb(path, bubbles):
    con = sqlite3.connect(path)
    con.execute("create table cursorDiskKV (key text, value text)")
    for key, value in bubbles:
        con.execute("insert into cursorDiskKV values (?, ?)", (key, value))
    con.commit()
    con.close()


def test_not_available_without_state_vscdb(tmp_path):
    parser = CursorParser(root=tmp_path)
    assert parser.is_available() is False
    assert list(parser.read_events()) == []


def test_reads_bubbles_with_positive_token_count(tmp_path):
    make_state_vscdb(
        tmp_path / "state.vscdb",
        [
            (
                "bubbleId:composer-1:bubble-a",
                json.dumps({"tokenCount": 500, "modelName": "gpt-5"}),
            ),
            (
                "bubbleId:composer-1:bubble-b",
                json.dumps({"tokenCount": 0}),  # excluded: zero
            ),
            (
                "bubbleId:composer-1:bubble-c",
                json.dumps({"text": "no token count field here"}),  # excluded
            ),
            ("someOtherKey:x", json.dumps({"tokenCount": 999})),  # excluded: wrong prefix
        ],
    )

    parser = CursorParser(root=tmp_path)
    events = list(parser.read_events())

    assert len(events) == 1
    event = events[0]
    assert event.is_estimated is True
    assert event.session_id == "composer-1"
    assert event.input_tokens == 500
    assert event.model == "gpt-5"


def test_malformed_json_value_is_skipped(tmp_path):
    make_state_vscdb(tmp_path / "state.vscdb", [("bubbleId:c1:b1", "not valid json")])
    parser = CursorParser(root=tmp_path)
    assert list(parser.read_events()) == []
