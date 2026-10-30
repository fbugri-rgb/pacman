"""Tests for comment stripping, defaults and value clamping."""

from __future__ import annotations

import json

import pytest

from pacman.config import (
    ConfigError,
    DEFAULT_LEVEL_WIDTH,
    DEFAULT_LIVES,
    DEFAULT_PLAYER_SPEED,
    DEFAULT_SEED,
    DEFAULT_SUPER_PACGUM_DURATION,
    MAX_LEVEL_SIZE,
    MIN_LEVELS,
    MIN_LEVEL_SIZE,
    load_config,
    parse_config,
    strip_json_comments,
)


def test_hash_comments_are_ignored() -> None:
    text = '# a comment\n{"lives": 5}  # trailing\n'
    assert json.loads(strip_json_comments(text)) == {"lives": 5}


def test_c_and_cpp_comments_are_ignored() -> None:
    text = '/* block\ncomment */ {"lives": 5} // line\n'
    assert json.loads(strip_json_comments(text)) == {"lives": 5}


def test_comment_markers_inside_strings_survive() -> None:
    text = '{"highscore_filename": "a#b//c/*d*/e.json"}'
    parsed = json.loads(strip_json_comments(text))
    assert parsed["highscore_filename"] == "a#b//c/*d*/e.json"


def test_escaped_quote_does_not_end_the_string() -> None:
    text = r'{"highscore_filename": "a\"# b.json"}'
    parsed = json.loads(strip_json_comments(text))
    assert parsed["highscore_filename"] == 'a"# b.json'


def test_line_numbers_are_preserved() -> None:
    text = "# one\n# two\n{}\n"
    assert strip_json_comments(text).count("\n") == text.count("\n")


def test_unterminated_block_comment_does_not_raise() -> None:
    assert json.loads(strip_json_comments('{"lives": 2} /* never closed')) == {
        "lives": 2
    }


def test_empty_config_yields_defaults() -> None:
    config = parse_config("{}")
    assert config.lives == DEFAULT_LIVES
    assert len(config.levels) == MIN_LEVELS
    assert config.warnings


def test_unknown_keys_are_ignored() -> None:
    config = parse_config('{"totally_unknown": 12, "lives": 4}')
    assert config.lives == 4


def test_out_of_range_values_are_clamped() -> None:
    config = parse_config('{"lives": -7, "points_per_pacgum": -1}')
    assert config.lives == 1
    assert config.points_per_pacgum == 0
    assert len(config.warnings) >= 2


def test_wrong_type_falls_back_to_default() -> None:
    config = parse_config('{"lives": "three"}')
    assert config.lives == DEFAULT_LIVES
    assert any("lives" in warning for warning in config.warnings)


def test_booleans_are_not_accepted_as_numbers() -> None:
    config = parse_config('{"lives": true}')
    assert config.lives == DEFAULT_LIVES


def test_non_finite_numbers_fall_back_to_defaults() -> None:
    config = parse_config(
        '{"lives": 1e999, "seed": NaN, "player_speed": Infinity,'
        ' "super_pacgum_duration": NaN, "level": [{"width": -Infinity}]}'
    )
    assert config.lives == DEFAULT_LIVES
    assert config.seed == DEFAULT_SEED
    assert config.player_speed == DEFAULT_PLAYER_SPEED
    assert config.super_pacgum_duration == DEFAULT_SUPER_PACGUM_DURATION
    assert config.levels[0].width == DEFAULT_LEVEL_WIDTH
    assert sum("finite" in warning for warning in config.warnings) == 5


def test_missing_levels_are_reported_once() -> None:
    config = parse_config("{}")
    assert [w for w in config.warnings if w.startswith("'level'")] == [
        f"'level': no level defined; generating {MIN_LEVELS} defaults."
    ]


def test_level_sizes_are_clamped() -> None:
    config = parse_config(
        '{"level": [{"width": 1, "height": 9999}]}'
    )
    assert config.levels[0].width == MIN_LEVEL_SIZE
    assert config.levels[0].height == MAX_LEVEL_SIZE


def test_levels_are_padded_to_the_minimum() -> None:
    config = parse_config('{"level": [{"width": 9, "height": 9}]}')
    assert len(config.levels) == MIN_LEVELS
    assert config.levels[0].width == 9


def test_extra_levels_are_kept() -> None:
    entries = ",".join('{"width": 9, "height": 9}' for _ in range(14))
    config = parse_config(f'{{"level": [{entries}]}}')
    assert len(config.levels) == 14


def test_malformed_level_entry_falls_back() -> None:
    config = parse_config('{"level": ["oops"]}')
    assert len(config.levels) == MIN_LEVELS
    assert any("level[0]" in warning for warning in config.warnings)


def test_global_pacgum_is_inherited_by_levels() -> None:
    config = parse_config('{"pacgum": 77, "level": [{"width": 9}]}')
    assert config.levels[0].pacgum == 77


def test_level_overrides_global_pacgum() -> None:
    config = parse_config(
        '{"pacgum": 77, "level": [{"width": 9, "pacgum": 5}]}'
    )
    assert config.levels[0].pacgum == 5


def test_invalid_json_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        parse_config('{"lives": }')


def test_non_object_top_level_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        parse_config("[1, 2, 3]")


def test_deeply_nested_json_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        parse_config("[" * 100_000)


def test_missing_file_raises_config_error() -> None:
    with pytest.raises(ConfigError):
        load_config("definitely-missing-file.json")


def test_non_json_extension_is_rejected() -> None:
    with pytest.raises(ConfigError):
        load_config("config.txt")


def test_shipped_config_loads_without_warnings() -> None:
    config = load_config("config.json")
    assert config.warnings == ()
    assert len(config.levels) >= MIN_LEVELS
