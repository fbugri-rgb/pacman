"""Tests for the persistent highscore table."""

from __future__ import annotations

import json
from pathlib import Path

from pacman.highscores import (
    DEFAULT_NAME,
    HighscoreTable,
    MAX_ENTRIES,
    MAX_NAME_LENGTH,
    sanitize_name,
    sanitize_score,
)


def test_name_keeps_alphanumerics_and_spaces() -> None:
    assert sanitize_name("Bob 42") == "Bob 42"


def test_name_drops_other_characters() -> None:
    assert sanitize_name("B<o>b!/*") == "Bob"


def test_name_is_truncated() -> None:
    assert len(sanitize_name("A" * 50)) == MAX_NAME_LENGTH


def test_empty_name_falls_back() -> None:
    assert sanitize_name("!!!") == DEFAULT_NAME
    assert sanitize_name("   ") == DEFAULT_NAME


def test_score_rejects_negative_and_non_numbers() -> None:
    assert sanitize_score(-1) is None
    assert sanitize_score("12") is None
    assert sanitize_score(True) is None
    assert sanitize_score(12.9) == 12


def test_missing_file_is_not_an_error(tmp_path: Path) -> None:
    table = HighscoreTable(str(tmp_path / "nope.json"))
    table.load()
    assert table.entries == []
    assert table.warnings == []


def test_corrupt_file_is_recovered(tmp_path: Path) -> None:
    path = tmp_path / "scores.json"
    path.write_text("{not json at all", encoding="utf-8")
    table = HighscoreTable(str(path))
    table.load()
    assert table.entries == []
    assert table.warnings


def test_wrong_shape_is_recovered(tmp_path: Path) -> None:
    path = tmp_path / "scores.json"
    path.write_text('{"a": 1}', encoding="utf-8")
    table = HighscoreTable(str(path))
    table.load()
    assert table.entries == []
    assert table.warnings


def test_malformed_entries_are_dropped(tmp_path: Path) -> None:
    path = tmp_path / "scores.json"
    payload = [
        {"name": "OK", "score": 10},
        {"name": "NEG", "score": -5},
        {"score": 10},
        "nonsense",
    ]
    path.write_text(json.dumps(payload), encoding="utf-8")
    table = HighscoreTable(str(path))
    table.load()
    assert [entry.name for entry in table.entries] == ["OK"]
    assert table.warnings


def test_table_is_sorted_and_capped(tmp_path: Path) -> None:
    table = HighscoreTable(str(tmp_path / "scores.json"))
    for index in range(MAX_ENTRIES + 5):
        table.add(f"P{index}", index * 10)
    assert len(table.entries) == MAX_ENTRIES
    scores = [entry.score for entry in table.entries]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == (MAX_ENTRIES + 4) * 10


def test_qualifies_respects_the_cap(tmp_path: Path) -> None:
    table = HighscoreTable(str(tmp_path / "scores.json"))
    assert table.qualifies(0)
    for index in range(MAX_ENTRIES):
        table.add("P", 100)
    assert not table.qualifies(50)
    assert table.qualifies(101)
    assert not table.qualifies(-1)


def test_round_trip(tmp_path: Path) -> None:
    path = str(tmp_path / "scores.json")
    table = HighscoreTable(path)
    table.add("Fbugri", 4242)
    assert table.save()
    reloaded = HighscoreTable(path)
    reloaded.load()
    assert [(e.name, e.score) for e in reloaded.entries] == [("Fbugri", 4242)]


def test_negative_score_is_stored_as_zero(tmp_path: Path) -> None:
    table = HighscoreTable(str(tmp_path / "scores.json"))
    table.add("X", -10)
    assert table.entries[0].score == 0


def test_save_failure_is_reported(tmp_path: Path) -> None:
    unwritable = tmp_path / "scores.json"
    unwritable.mkdir()
    table = HighscoreTable(str(unwritable))
    table.add("X", 1)
    assert not table.save()
    assert table.warnings
