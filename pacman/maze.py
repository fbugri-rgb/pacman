"""Adapter around the assigned A-Maze-ing package.

The generator is a third-party package that must be used as-is, so every
call into it goes through this module.  It is treated as an untrusted
boundary: the constructor signature is probed, the returned grid is
validated, and any failure is reported as a :class:`MazeError` instead of
escaping as an arbitrary exception.

The generator works on *cells* that carry their four walls in four bits.
Pac-Man needs walls that occupy real squares, so a ``w * h`` cell maze is
expanded into a ``(2w + 1) * (2h + 1)`` tile grid where odd coordinates
are cell centres and even coordinates are the walls between them.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import random
from dataclasses import dataclass
from typing import Callable, Iterable

from .constants import (
    CELL_ISOLATED,
    Tile,
    WALL_EAST,
    WALL_NORTH,
    WALL_SOUTH,
    WALL_WEST,
)

Position = tuple[int, int]

GHOST_COUNT = 4


class MazeError(Exception):
    """Raised when the maze generator cannot produce a usable maze."""


@dataclass(frozen=True)
class Level:
    """A ready to play level.

    Attributes:
        tiles: Row-major grid of walls and corridors, indexed ``[y][x]``.
        player_spawn: Where the player starts and respawns.
        ghost_spawns: Starting corner of each ghost.
        pacgums: Tiles holding a normal pacgum.
        super_pacgums: Tiles holding a super-pacgum.
        seed: Seed handed to the generator for this maze.
    """

    tiles: tuple[tuple[Tile, ...], ...]
    player_spawn: Position
    ghost_spawns: tuple[Position, ...]
    pacgums: frozenset[Position]
    super_pacgums: frozenset[Position]
    seed: int

    @property
    def cols(self) -> int:
        """Return the grid width in tiles."""
        return len(self.tiles[0])

    @property
    def rows(self) -> int:
        """Return the grid height in tiles."""
        return len(self.tiles)

    def is_wall(self, x: int, y: int) -> bool:
        """Tell whether the tile at ``(x, y)`` blocks movement.

        Out of bounds coordinates count as walls, so callers never need a
        separate bounds check.

        Args:
            x: Column index.
            y: Row index.

        Returns:
            ``True`` if nothing can walk there.
        """
        if not (0 <= y < self.rows and 0 <= x < self.cols):
            return True
        return self.tiles[y][x] is Tile.WALL


def _generator_class() -> Callable[..., object]:
    """Import ``MazeGenerator`` from the assigned package.

    Returns:
        The generator class.

    Raises:
        MazeError: If the package is missing or does not expose the class.
    """
    try:
        module = importlib.import_module("mazegenerator")
    except ImportError as exc:
        raise MazeError(
            "the 'mazegenerator' package is not installed "
            f"({exc}); run 'make install' first"
        ) from exc
    generator = getattr(module, "MazeGenerator", None)
    if not isinstance(generator, type):
        raise MazeError(
            "the 'mazegenerator' package does not expose a MazeGenerator "
            "class"
        )
    return generator


def _instantiate(width: int, height: int, seed: int) -> object:
    """Build a generator instance, probing the constructor signature.

    The package documentation and its implementation disagree on the
    argument names, so several spellings are tried before giving up.
    Anything the generator prints while building is discarded.

    Args:
        width: Maze width in cells.
        height: Maze height in cells.
        seed: Seed passed to the generator.

    Returns:
        A freshly generated maze object.

    Raises:
        MazeError: If no accepted signature could be found, or if the
            generator raised while building the maze.
    """
    generator = _generator_class()
    candidates: tuple[dict[str, object], ...] = (
        {"size": (width, height), "perfect": False, "seed": seed},
        {"width": width, "height": height, "perfect": False, "seed": seed},
        {"size": (width, height), "perfect": False},
        {"size": (width, height)},
    )
    signature_errors: list[str] = []
    for kwargs in candidates:
        try:
            # The generator prints a cosmetic warning on stdout when the
            # maze is too small for its '42' logo; the maze is still fine.
            with contextlib.redirect_stdout(io.StringIO()):
                return generator(**kwargs)
        except TypeError as exc:
            signature_errors.append(str(exc))
        except RecursionError as exc:
            raise MazeError(
                f"the generator exhausted the stack on a {width}x{height} "
                f"maze ({exc})"
            ) from exc
        except Exception as exc:
            # Deliberately broad: the generator is third-party code and
            # may raise anything, but the game must never crash on it.
            raise MazeError(
                f"the maze generator failed on a {width}x{height} maze: "
                f"{exc}"
            ) from exc
    raise MazeError(
        "no supported MazeGenerator constructor signature: "
        + "; ".join(signature_errors)
    )


def _read_grid(maze: object) -> list[list[int]]:
    """Extract and validate the wall grid from a generator instance.

    The dimensions are read back from the grid itself rather than assumed,
    so a generator that adjusts the requested size still works.

    Args:
        maze: The object returned by the generator.

    Returns:
        A rectangular grid of wall bitmasks, indexed ``[y][x]``.

    Raises:
        MazeError: If the grid is absent, empty, ragged or not numeric.
    """
    raw = getattr(maze, "maze", None)
    if not isinstance(raw, list) or not raw:
        raise MazeError("the maze generator returned an empty maze")
    grid: list[list[int]] = []
    for row in raw:
        if not isinstance(row, list) or not row:
            raise MazeError("the maze generator returned a malformed row")
        cells: list[int] = []
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int):
                raise MazeError(
                    "the maze generator returned a non-integer cell"
                )
            cells.append(cell)
        if grid and len(cells) != len(grid[0]):
            raise MazeError("the maze generator returned a ragged grid")
        grid.append(cells)
    return grid


def _to_tiles(grid: list[list[int]]) -> list[list[Tile]]:
    """Expand a cell/wall-bit grid into a walkable tile grid.

    A passage is carved only when both neighbouring cells agree that no
    wall separates them, which keeps the result consistent even if the
    generator leaves a cell in a half-initialised state.

    Args:
        grid: Wall bitmasks indexed ``[y][x]``.

    Returns:
        A ``(2w + 1) * (2h + 1)`` grid of tiles.
    """
    height = len(grid)
    width = len(grid[0])
    rows = 2 * height + 1
    cols = 2 * width + 1
    tiles = [[Tile.WALL for _ in range(cols)] for _ in range(rows)]
    for cell_y in range(height):
        for cell_x in range(width):
            value = grid[cell_y][cell_x]
            if value & CELL_ISOLATED == CELL_ISOLATED:
                continue
            tiles[2 * cell_y + 1][2 * cell_x + 1] = Tile.CORRIDOR
            if cell_x + 1 < width:
                neighbour = grid[cell_y][cell_x + 1]
                if not value & WALL_EAST and not neighbour & WALL_WEST:
                    tiles[2 * cell_y + 1][2 * cell_x + 2] = Tile.CORRIDOR
            if cell_y + 1 < height:
                neighbour = grid[cell_y + 1][cell_x]
                if not value & WALL_SOUTH and not neighbour & WALL_NORTH:
                    tiles[2 * cell_y + 2][2 * cell_x + 1] = Tile.CORRIDOR
    return tiles


def _neighbours(position: Position) -> Iterable[Position]:
    """Yield the four tiles orthogonally adjacent to ``position``.

    Args:
        position: The tile to look around.

    Returns:
        An iterable of adjacent tile coordinates.
    """
    x, y = position
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def _largest_component(tiles: list[list[Tile]]) -> set[Position]:
    """Return the biggest group of mutually reachable corridor tiles.

    Everything the player can interact with is placed inside this group,
    which guarantees that every pacgum can actually be collected.

    Args:
        tiles: The tile grid.

    Returns:
        The tiles of the largest connected corridor area.

    Raises:
        MazeError: If the maze contains no corridor at all.
    """
    rows = len(tiles)
    cols = len(tiles[0])
    remaining = {
        (x, y)
        for y in range(rows)
        for x in range(cols)
        if tiles[y][x] is Tile.CORRIDOR
    }
    if not remaining:
        raise MazeError("the generated maze has no corridor")
    best: set[Position] = set()
    while remaining:
        start = next(iter(remaining))
        component: set[Position] = {start}
        stack = [start]
        remaining.discard(start)
        while stack:
            current = stack.pop()
            for neighbour in _neighbours(current):
                if neighbour in remaining:
                    remaining.discard(neighbour)
                    component.add(neighbour)
                    stack.append(neighbour)
        if len(component) > len(best):
            best = component
    return best


def _closest(
    candidates: set[Position], target: Position, taken: set[Position]
) -> Position:
    """Pick the candidate nearest to ``target``, avoiding taken tiles.

    Args:
        candidates: Tiles to choose from; must not be empty.
        target: The ideal position, which may itself be a wall.
        taken: Tiles already assigned to something else.

    Returns:
        The free candidate closest to ``target``, or the closest candidate
        overall when every one of them is already taken.
    """
    def distance(position: Position) -> int:
        return (position[0] - target[0]) ** 2 + (position[1] - target[1]) ** 2

    free = candidates - taken
    return min(free or candidates, key=distance)


def _corner_targets(cols: int, rows: int) -> tuple[Position, ...]:
    """Return the four extreme corners of the tile grid.

    Args:
        cols: Grid width in tiles.
        rows: Grid height in tiles.

    Returns:
        Top-left, top-right, bottom-left and bottom-right coordinates.
    """
    return ((0, 0), (cols - 1, 0), (0, rows - 1), (cols - 1, rows - 1))


def _populate(
    tiles: list[list[Tile]], pacgum_count: int, rng: random.Random
) -> tuple[Position, tuple[Position, ...], frozenset[Position],
           frozenset[Position]]:
    """Place the player, the ghosts and every collectible.

    Args:
        tiles: The tile grid.
        pacgum_count: How many normal pacgums to scatter.
        rng: Random source used to spread the pacgums.

    Returns:
        The player spawn, the four ghost spawns, the pacgum tiles and the
        super-pacgum tiles.

    Raises:
        MazeError: If the maze has no reachable corridor.
    """
    rows = len(tiles)
    cols = len(tiles[0])
    playable = _largest_component(tiles)
    taken: set[Position] = set()

    player_spawn = _closest(playable, (cols // 2, rows // 2), taken)
    taken.add(player_spawn)

    corners = _corner_targets(cols, rows)
    ghost_spawns: list[Position] = []
    for corner in corners:
        spawn = _closest(playable, corner, taken)
        taken.add(spawn)
        ghost_spawns.append(spawn)

    super_pacgums: set[Position] = set()
    for corner in corners:
        gum = _closest(playable, corner, taken)
        taken.add(gum)
        super_pacgums.add(gum)

    candidates = sorted(playable - {player_spawn} - super_pacgums)
    rng.shuffle(candidates)
    pacgums = frozenset(candidates[:max(pacgum_count, 0)])
    if not pacgums and candidates:
        pacgums = frozenset(candidates[:1])
    return (
        player_spawn,
        tuple(ghost_spawns),
        pacgums,
        frozenset(super_pacgums),
    )


def build_level(
    width: int, height: int, pacgum_count: int, seed: int
) -> Level:
    """Generate one level with the assigned A-Maze-ing package.

    ``perfect`` is always ``False`` so the maze contains loops and no dead
    end, which is what makes it playable as a Pac-Man board.

    Args:
        width: Maze width in generator cells.
        height: Maze height in generator cells.
        pacgum_count: How many normal pacgums to scatter.
        seed: Seed handed to the generator.

    Returns:
        A level ready to be played.

    Raises:
        MazeError: If the generator failed or produced an unusable maze.
    """
    maze = _instantiate(width, height, seed)
    grid = _read_grid(maze)
    tiles = _to_tiles(grid)
    # The generator reseeds the global random module, so placement uses a
    # private stream to stay independent from it.
    rng = random.Random(seed)
    player_spawn, ghost_spawns, pacgums, super_pacgums = _populate(
        tiles, pacgum_count, rng
    )
    return Level(
        tiles=tuple(tuple(row) for row in tiles),
        player_spawn=player_spawn,
        ghost_spawns=ghost_spawns,
        pacgums=pacgums,
        super_pacgums=super_pacgums,
        seed=seed,
    )
