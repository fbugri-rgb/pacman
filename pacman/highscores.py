"""Persistent top-ten highscore table.

Scores are kept in a small JSON file next to the game.  Every read is
defensive: a missing, unreadable or corrupted file simply yields an empty
table rather than an error, so a broken save can never stop the game.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Final

MAX_ENTRIES: Final[int] = 10
MAX_NAME_LENGTH: Final[int] = 10
DEFAULT_NAME: Final[str] = "PLAYER"


@dataclass(frozen=True)
class Entry:
    """One line of the highscore table.

    Attributes:
        name: Player name, at most ``MAX_NAME_LENGTH`` characters.
        score: Non-negative score.
    """

    name: str
    score: int


def sanitize_name(raw: str) -> str:
    """Reduce a player name to what the table accepts.

    Only alphanumeric characters and spaces survive, the result is
    trimmed to ``MAX_NAME_LENGTH`` characters, and an empty result falls
    back to ``DEFAULT_NAME``.

    Args:
        raw: The name typed by the player.

    Returns:
        A name that is safe to store.
    """
    kept = [char for char in raw if char.isalnum() or char == " "]
    name = "".join(kept)[:MAX_NAME_LENGTH].strip()
    return name if name else DEFAULT_NAME


def sanitize_score(raw: object) -> int | None:
    """Validate a score read from disk.

    Args:
        raw: The value found in the save file.

    Returns:
        The score as a non-negative integer, or ``None`` if unusable.
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    score = int(raw)
    return score if score >= 0 else None


class HighscoreTable:
    """The persistent list of the ten best scores.

    Attributes:
        path: Where the table is stored on disk.
        warnings: Messages describing recovered file problems.
    """

    def __init__(self, path: str) -> None:
        """Create a table backed by ``path``.

        The file is not read yet; call :meth:`load` for that.

        Args:
            path: Path of the JSON save file.
        """
        self.path: str = path
        self.warnings: list[str] = []
        self._entries: list[Entry] = []

    @property
    def entries(self) -> list[Entry]:
        """Return the current entries, best score first."""
        return list(self._entries)

    def load(self) -> None:
        """Read the table from disk, tolerating every kind of corruption.

        A missing file is normal on a first run and is not reported.  Any
        other problem is recorded in :attr:`warnings` and leaves the table
        empty rather than propagating an error.
        """
        self._entries = []
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.warnings.append(
                f"highscores: cannot read '{self.path}' ({exc}); "
                "starting from an empty table."
            )
            return
        if not isinstance(raw, list):
            self.warnings.append(
                f"highscores: '{self.path}' does not contain a list; "
                "starting from an empty table."
            )
            return
        self._entries = self._decode(raw)
        self._sort()

    def _decode(self, raw: list[object]) -> list[Entry]:
        """Turn raw JSON records into valid entries, dropping bad ones.

        Args:
            raw: The list read from the save file.

        Returns:
            Every record that could be understood.
        """
        entries: list[Entry] = []
        dropped = 0
        for record in raw:
            if not isinstance(record, dict):
                dropped += 1
                continue
            name = record.get("name")
            score = sanitize_score(record.get("score"))
            if not isinstance(name, str) or score is None:
                dropped += 1
                continue
            entries.append(Entry(sanitize_name(name), score))
        if dropped:
            self.warnings.append(
                f"highscores: ignored {dropped} malformed entrie(s) in "
                f"'{self.path}'."
            )
        return entries

    def _sort(self) -> None:
        """Sort by descending score and keep only the top entries."""
        self._entries.sort(key=lambda entry: entry.score, reverse=True)
        del self._entries[MAX_ENTRIES:]

    def qualifies(self, score: int) -> bool:
        """Tell whether ``score`` would make it into the table.

        Args:
            score: The score to test.

        Returns:
            ``True`` if the score deserves a place.
        """
        if score < 0:
            return False
        if len(self._entries) < MAX_ENTRIES:
            return True
        return score > self._entries[-1].score

    def add(self, name: str, score: int) -> None:
        """Insert a score in the table, keeping only the ten best.

        Args:
            name: Raw player name; it is sanitized before storage.
            score: The score to record; negative values become zero.
        """
        self._entries.append(Entry(sanitize_name(name), max(score, 0)))
        self._sort()

    def save(self) -> bool:
        """Write the table to disk atomically.

        The data is written to a temporary file in the same directory and
        then renamed, so an interrupted save cannot truncate the previous
        table.

        Returns:
            ``True`` on success, ``False`` if the file could not be written
            (the reason is appended to :attr:`warnings`).
        """
        payload = [
            {"name": entry.name, "score": entry.score}
            for entry in self._entries
        ]
        directory = os.path.dirname(os.path.abspath(self.path))
        temp_path = ""
        try:
            os.makedirs(directory, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=directory, delete=False,
                prefix=".highscores-", suffix=".tmp",
            ) as handle:
                temp_path = handle.name
                json.dump(payload, handle, indent=2)
                handle.write("\n")
            os.replace(temp_path, self.path)
            return True
        except OSError as exc:
            self.warnings.append(
                f"highscores: cannot write '{self.path}' ({exc}); "
                "this session will not be saved."
            )
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            return False
