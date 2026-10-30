"""Configuration loading, comment stripping and validation.

The game is configured through a single JSON file passed on the command
line.  On top of standard JSON this loader accepts comments, and it never
raises on a malformed value: anything missing or out of range is clamped
to a safe default and reported through :attr:`GameConfig.warnings`.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Final

DEFAULT_HIGHSCORE_FILENAME: Final[str] = "highscores.json"
DEFAULT_LIVES: Final[int] = 3
DEFAULT_PACGUM: Final[int] = 42
DEFAULT_POINTS_PACGUM: Final[int] = 10
DEFAULT_POINTS_SUPER_PACGUM: Final[int] = 50
DEFAULT_POINTS_GHOST: Final[int] = 200
DEFAULT_SEED: Final[int] = 42
DEFAULT_LEVEL_MAX_TIME: Final[int] = 90
DEFAULT_LEVEL_WIDTH: Final[int] = 15
DEFAULT_LEVEL_HEIGHT: Final[int] = 15
DEFAULT_PLAYER_SPEED: Final[float] = 6.0
DEFAULT_GHOST_SPEED: Final[float] = 4.5
DEFAULT_SUPER_PACGUM_DURATION: Final[float] = 8.0
DEFAULT_GHOST_RESPAWN_DELAY: Final[float] = 6.0

MIN_LEVELS: Final[int] = 10
MIN_LEVEL_SIZE: Final[int] = 7
MAX_LEVEL_SIZE: Final[int] = 35
MAX_LIVES: Final[int] = 99
MAX_POINTS: Final[int] = 100_000
MAX_SEED: Final[int] = 2**31 - 1
MIN_LEVEL_TIME: Final[int] = 10
MAX_LEVEL_TIME: Final[int] = 3600
MIN_SPEED: Final[float] = 1.0
MAX_SPEED: Final[float] = 20.0
MAX_DURATION: Final[float] = 120.0


@dataclass(frozen=True)
class LevelConfig:
    """Parameters of a single level.

    Attributes:
        width: Maze width in generator cells.
        height: Maze height in generator cells.
        pacgum: Number of pacgums to scatter in the corridors.
        max_time: Time limit of the level, in seconds.
        ghost_speed: Ghost speed for this level, in tiles per second.
    """

    width: int
    height: int
    pacgum: int
    max_time: int
    ghost_speed: float


@dataclass(frozen=True)
class GameConfig:
    """Fully validated game configuration.

    Every field is guaranteed to hold a usable value: the loader clamps
    anything invalid rather than failing.

    Attributes:
        highscore_filename: Path of the persistent highscore file.
        levels: Ordered level definitions, at least ``MIN_LEVELS`` long.
        lives: Number of lives the player starts with.
        points_per_pacgum: Score awarded for a pacgum.
        points_per_super_pacgum: Score awarded for a super-pacgum.
        points_per_ghost: Score awarded for an edible ghost.
        seed: Seed of the first level; later levels are random.
        player_speed: Player speed in tiles per second.
        super_pacgum_duration: How long ghosts stay edible, in seconds.
        ghost_respawn_delay: Delay before an eaten ghost returns, seconds.
        cheats_enabled: Whether the cheat keys are active.
        warnings: Human readable messages about corrected values.
    """

    highscore_filename: str = DEFAULT_HIGHSCORE_FILENAME
    levels: tuple[LevelConfig, ...] = ()
    lives: int = DEFAULT_LIVES
    points_per_pacgum: int = DEFAULT_POINTS_PACGUM
    points_per_super_pacgum: int = DEFAULT_POINTS_SUPER_PACGUM
    points_per_ghost: int = DEFAULT_POINTS_GHOST
    seed: int = DEFAULT_SEED
    player_speed: float = DEFAULT_PLAYER_SPEED
    super_pacgum_duration: float = DEFAULT_SUPER_PACGUM_DURATION
    ghost_respawn_delay: float = DEFAULT_GHOST_RESPAWN_DELAY
    cheats_enabled: bool = True
    warnings: tuple[str, ...] = field(default_factory=tuple)


class ConfigError(Exception):
    """Raised when the configuration file cannot be read at all."""


def strip_json_comments(text: str) -> str:
    """Remove comments from a JSON document.

    Three comment styles are accepted outside of string literals: ``#``
    and ``//`` run to the end of the line, and ``/* ... */`` spans lines.
    Comment characters are replaced by spaces so that the byte offsets
    reported by :mod:`json` still point at the right place.

    Args:
        text: Raw file contents.

    Returns:
        The same document with every comment blanked out.
    """
    out: list[str] = []
    index = 0
    length = len(text)
    in_string = False
    while index < length:
        char = text[index]
        if in_string:
            out.append(char)
            if char == "\\" and index + 1 < length:
                out.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        two = text[index:index + 2]
        if char == "#" or two == "//":
            while index < length and text[index] != "\n":
                out.append(" ")
                index += 1
            continue
        if two == "/*":
            end = text.find("*/", index + 2)
            end = length if end == -1 else end + 2
            for skipped in text[index:end]:
                out.append("\n" if skipped == "\n" else " ")
            index = end
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _as_int(
    value: object,
    key: str,
    default: int,
    low: int,
    high: int,
    warnings: list[str],
) -> int:
    """Coerce ``value`` to an int inside ``[low, high]``.

    Args:
        value: Raw value read from the config, or ``None`` if absent.
        key: Key name, used in warning messages.
        default: Value used when ``value`` is absent or unusable.
        low: Lowest accepted value.
        high: Highest accepted value.
        warnings: List collecting the messages produced along the way.

    Returns:
        A valid integer.
    """
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warnings.append(
            f"'{key}': expected a number, got {type(value).__name__}; "
            f"using {default}."
        )
        return default
    if isinstance(value, float) and not math.isfinite(value):
        warnings.append(
            f"'{key}': {value} is not a finite number; using {default}."
        )
        return default
    number = int(value)
    if number < low or number > high:
        clamped = min(max(number, low), high)
        warnings.append(
            f"'{key}': {number} is out of range [{low}, {high}]; "
            f"clamped to {clamped}."
        )
        return clamped
    return number


def _as_float(
    value: object,
    key: str,
    default: float,
    low: float,
    high: float,
    warnings: list[str],
) -> float:
    """Coerce ``value`` to a float inside ``[low, high]``.

    Args:
        value: Raw value read from the config, or ``None`` if absent.
        key: Key name, used in warning messages.
        default: Value used when ``value`` is absent or unusable.
        low: Lowest accepted value.
        high: Highest accepted value.
        warnings: List collecting the messages produced along the way.

    Returns:
        A valid float.
    """
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warnings.append(
            f"'{key}': expected a number, got {type(value).__name__}; "
            f"using {default}."
        )
        return default
    number = float(value)
    if not math.isfinite(number):
        warnings.append(
            f"'{key}': {number} is not a finite number; using {default}."
        )
        return default
    if number < low or number > high:
        clamped = min(max(number, low), high)
        warnings.append(
            f"'{key}': {number} is out of range [{low}, {high}]; "
            f"clamped to {clamped}."
        )
        return clamped
    return number


def _as_bool(
    value: object, key: str, default: bool, warnings: list[str]
) -> bool:
    """Coerce ``value`` to a boolean.

    Args:
        value: Raw value read from the config, or ``None`` if absent.
        key: Key name, used in warning messages.
        default: Value used when ``value`` is absent or unusable.
        warnings: List collecting the messages produced along the way.

    Returns:
        A valid boolean.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    warnings.append(f"'{key}': expected true or false; using {default}.")
    return default


def _as_filename(value: object, warnings: list[str]) -> str:
    """Validate the highscore filename.

    Args:
        value: Raw value read from the config, or ``None`` if absent.
        warnings: List collecting the messages produced along the way.

    Returns:
        A non-empty filename.
    """
    if value is None:
        return DEFAULT_HIGHSCORE_FILENAME
    if not isinstance(value, str) or not value.strip():
        warnings.append(
            "'highscore_filename': expected a non-empty string; "
            f"using '{DEFAULT_HIGHSCORE_FILENAME}'."
        )
        return DEFAULT_HIGHSCORE_FILENAME
    return value.strip()


def _parse_level(
    raw: object,
    index: int,
    fallback_pacgum: int,
    fallback_time: int,
    warnings: list[str],
) -> LevelConfig:
    """Build a :class:`LevelConfig` from one entry of the ``level`` array.

    Args:
        raw: The raw level entry.
        index: Zero based position of the level, for warning messages.
        fallback_pacgum: Global pacgum count used when not overridden.
        fallback_time: Global time limit used when not overridden.
        warnings: List collecting the messages produced along the way.

    Returns:
        A valid level definition.
    """
    label = f"level[{index}]"
    if not isinstance(raw, dict):
        warnings.append(f"'{label}': expected an object; using defaults.")
        entry: dict[str, object] = {}
    else:
        entry = raw
    width = _as_int(
        entry.get("width"), f"{label}.width", DEFAULT_LEVEL_WIDTH,
        MIN_LEVEL_SIZE, MAX_LEVEL_SIZE, warnings,
    )
    height = _as_int(
        entry.get("height"), f"{label}.height", DEFAULT_LEVEL_HEIGHT,
        MIN_LEVEL_SIZE, MAX_LEVEL_SIZE, warnings,
    )
    pacgum = _as_int(
        entry.get("pacgum"), f"{label}.pacgum", fallback_pacgum,
        1, MAX_POINTS, warnings,
    )
    max_time = _as_int(
        entry.get("max_time"), f"{label}.max_time", fallback_time,
        MIN_LEVEL_TIME, MAX_LEVEL_TIME, warnings,
    )
    ghost_speed = _as_float(
        entry.get("ghost_speed"), f"{label}.ghost_speed", DEFAULT_GHOST_SPEED,
        MIN_SPEED, MAX_SPEED, warnings,
    )
    return LevelConfig(width, height, pacgum, max_time, ghost_speed)


def _grown(level: LevelConfig, step: int) -> LevelConfig:
    """Derive a slightly harder level from an existing one.

    Used to pad the level list up to the mandatory minimum length.

    Args:
        level: The level to grow from.
        step: How many levels past ``level`` this one is.

    Returns:
        A larger, faster level.
    """
    width = min(level.width + 2 * step, MAX_LEVEL_SIZE)
    height = min(level.height + 2 * step, MAX_LEVEL_SIZE)
    speed = min(level.ghost_speed + 0.2 * step, MAX_SPEED)
    return LevelConfig(width, height, level.pacgum, level.max_time, speed)


def _parse_levels(
    raw: object, pacgum: int, max_time: int, warnings: list[str]
) -> tuple[LevelConfig, ...]:
    """Build the level list, padding it to at least ``MIN_LEVELS`` entries.

    Args:
        raw: The raw ``level`` value from the config.
        pacgum: Global pacgum count.
        max_time: Global time limit.
        warnings: List collecting the messages produced along the way.

    Returns:
        A tuple of at least ``MIN_LEVELS`` level definitions.
    """
    entries: list[object]
    if raw is None:
        entries = []
    elif isinstance(raw, list):
        entries = list(raw)
    else:
        warnings.append("'level': expected an array; ignoring it.")
        entries = []
    levels = [
        _parse_level(entry, index, pacgum, max_time, warnings)
        for index, entry in enumerate(entries)
    ]
    if not levels:
        warnings.append(
            f"'level': no level defined; generating {MIN_LEVELS} defaults."
        )
        levels.append(
            LevelConfig(
                DEFAULT_LEVEL_WIDTH, DEFAULT_LEVEL_HEIGHT, pacgum, max_time,
                DEFAULT_GHOST_SPEED,
            )
        )
    elif len(levels) < MIN_LEVELS:
        warnings.append(
            f"'level': only {len(levels)} level(s) defined; padding to "
            f"{MIN_LEVELS}."
        )
    while len(levels) < MIN_LEVELS:
        levels.append(_grown(levels[-1], 1))
    return tuple(levels)


def parse_config(text: str) -> GameConfig:
    """Parse the contents of a configuration file.

    Args:
        text: Raw file contents, comments included.

    Returns:
        A fully validated configuration.

    Raises:
        ConfigError: If the document is not valid JSON once comments are
            stripped, is nested too deeply to parse, or if its top level
            is not an object.
    """
    warnings: list[str] = []
    try:
        parsed = json.loads(strip_json_comments(text))
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except RecursionError as exc:
        raise ConfigError("the config is nested too deeply") from exc
    if not isinstance(parsed, dict):
        raise ConfigError("the top level of the config must be an object")
    data: dict[str, object] = parsed

    pacgum = _as_int(
        data.get("pacgum"), "pacgum", DEFAULT_PACGUM, 1, MAX_POINTS, warnings,
    )
    max_time = _as_int(
        data.get("level_max_time"), "level_max_time", DEFAULT_LEVEL_MAX_TIME,
        MIN_LEVEL_TIME, MAX_LEVEL_TIME, warnings,
    )
    return GameConfig(
        highscore_filename=_as_filename(
            data.get("highscore_filename"), warnings
        ),
        levels=_parse_levels(data.get("level"), pacgum, max_time, warnings),
        lives=_as_int(
            data.get("lives"), "lives", DEFAULT_LIVES, 1, MAX_LIVES, warnings,
        ),
        points_per_pacgum=_as_int(
            data.get("points_per_pacgum"), "points_per_pacgum",
            DEFAULT_POINTS_PACGUM, 0, MAX_POINTS, warnings,
        ),
        points_per_super_pacgum=_as_int(
            data.get("points_per_super_pacgum"), "points_per_super_pacgum",
            DEFAULT_POINTS_SUPER_PACGUM, 0, MAX_POINTS, warnings,
        ),
        points_per_ghost=_as_int(
            data.get("points_per_ghost"), "points_per_ghost",
            DEFAULT_POINTS_GHOST, 0, MAX_POINTS, warnings,
        ),
        seed=_as_int(
            data.get("seed"), "seed", DEFAULT_SEED, 1, MAX_SEED, warnings,
        ),
        player_speed=_as_float(
            data.get("player_speed"), "player_speed", DEFAULT_PLAYER_SPEED,
            MIN_SPEED, MAX_SPEED, warnings,
        ),
        super_pacgum_duration=_as_float(
            data.get("super_pacgum_duration"), "super_pacgum_duration",
            DEFAULT_SUPER_PACGUM_DURATION, 0.5, MAX_DURATION, warnings,
        ),
        ghost_respawn_delay=_as_float(
            data.get("ghost_respawn_delay"), "ghost_respawn_delay",
            DEFAULT_GHOST_RESPAWN_DELAY, 0.5, MAX_DURATION, warnings,
        ),
        cheats_enabled=_as_bool(
            data.get("cheats_enabled"), "cheats_enabled", True, warnings,
        ),
        warnings=tuple(warnings),
    )


def load_config(path: str) -> GameConfig:
    """Read and validate the configuration file at ``path``.

    Args:
        path: Path to the JSON configuration file.

    Returns:
        A fully validated configuration.

    Raises:
        ConfigError: If the file cannot be read or is not valid JSON.
    """
    if not path.lower().endswith(".json"):
        raise ConfigError(f"'{path}' is not a .json file")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except FileNotFoundError as exc:
        raise ConfigError(f"no such file: '{path}'") from exc
    except IsADirectoryError as exc:
        raise ConfigError(f"'{path}' is a directory, not a file") from exc
    except PermissionError as exc:
        raise ConfigError(f"permission denied while reading '{path}'") from exc
    except UnicodeDecodeError as exc:
        raise ConfigError(f"'{path}' is not valid UTF-8 text") from exc
    except OSError as exc:
        raise ConfigError(f"cannot read '{path}': {exc.strerror}") from exc
    return parse_config(text)
