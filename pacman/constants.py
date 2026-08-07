"""Shared constants, enumerations and small value types.

This module holds every value that is used across several parts of the
game and that is not user configurable.  Anything the player can tune
lives in :mod:`pacman.config` instead.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

Color = tuple[int, int, int]

WINDOW_WIDTH: Final[int] = 1000
WINDOW_HEIGHT: Final[int] = 760
HUD_HEIGHT: Final[int] = 56
TARGET_FPS: Final[int] = 60

TITLE: Final[str] = "Pac-Man - Ghosts! More ghosts!"

COLOR_BACKGROUND: Final[Color] = (0, 0, 0)
COLOR_WALL: Final[Color] = (33, 33, 222)
COLOR_WALL_EDGE: Final[Color] = (66, 110, 255)
COLOR_PACGUM: Final[Color] = (255, 203, 153)
COLOR_SUPER_PACGUM: Final[Color] = (255, 255, 120)
COLOR_PLAYER: Final[Color] = (255, 255, 0)
COLOR_TEXT: Final[Color] = (255, 255, 255)
COLOR_TEXT_DIM: Final[Color] = (150, 150, 160)
COLOR_HIGHLIGHT: Final[Color] = (255, 224, 66)
COLOR_FRIGHTENED: Final[Color] = (36, 36, 200)
COLOR_FRIGHTENED_BLINK: Final[Color] = (240, 240, 240)
COLOR_DANGER: Final[Color] = (255, 80, 80)
COLOR_SUCCESS: Final[Color] = (120, 255, 140)

GHOST_COLORS: Final[tuple[Color, Color, Color, Color]] = (
    (255, 0, 0),        # Blinky
    (255, 184, 222),    # Pinky
    (0, 255, 222),      # Inky
    (255, 184, 82),     # Clyde
)
GHOST_NAMES: Final[tuple[str, str, str, str]] = (
    "Blinky", "Pinky", "Inky", "Clyde",
)

# Wall bits used by the assigned A-Maze-ing package.  Documented in its
# README: each cell stores its four walls in the four low bits.
WALL_NORTH: Final[int] = 1
WALL_EAST: Final[int] = 2
WALL_SOUTH: Final[int] = 4
WALL_WEST: Final[int] = 8
# A cell whose four walls are closed is an isolated cell: the generator
# uses that value for the '42' pattern it draws inside every maze.
CELL_ISOLATED: Final[int] = 15


class Tile(Enum):
    """A single square of the playable grid."""

    WALL = 0
    CORRIDOR = 1


class Direction(Enum):
    """The four directions an actor may face, as (dx, dy) tile deltas."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self) -> tuple[int, int]:
        """Return the (dx, dy) tile offset for this direction."""
        dx, dy = self.value
        return dx, dy

    @property
    def opposite(self) -> "Direction":
        """Return the direction facing the other way."""
        dx, dy = self.value
        return _OPPOSITES[(-dx, -dy)]


_OPPOSITES: Final[dict[tuple[int, int], Direction]] = {
    d.value: d for d in Direction
}


class GhostState(Enum):
    """Lifecycle of a ghost during a level."""

    CHASE = "chase"
    FRIGHTENED = "frightened"
    EATEN = "eaten"


class Screen(Enum):
    """Top level screens of the application state machine."""

    MENU = "menu"
    HIGHSCORES = "highscores"
    INSTRUCTIONS = "instructions"
    PLAYING = "playing"
    PAUSED = "paused"
    LEVEL_CLEARED = "level_cleared"
    NAME_ENTRY = "name_entry"
    ERROR = "error"
    QUIT = "quit"
