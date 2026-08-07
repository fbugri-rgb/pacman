"""Tests for the A-Maze-ing adapter and the tile grid it produces."""

from __future__ import annotations

import importlib
from collections import deque

import pytest

from pacman.constants import Tile
from pacman.maze import Level, MazeError, Position, build_level

pytest.importorskip("mazegenerator")

SIZES = (7, 11, 15, 21)
SEEDS = (1, 42, 4242)


def reachable(level: Level, start: Position) -> set[Position]:
    """Return every corridor tile reachable from ``start``."""
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for neighbour in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if neighbour not in seen and not level.is_wall(*neighbour):
                seen.add(neighbour)
                queue.append(neighbour)
    return seen


def test_tile_grid_is_twice_the_cell_grid_plus_one() -> None:
    level = build_level(11, 13, 50, 42)
    assert level.cols == 2 * 11 + 1
    assert level.rows == 2 * 13 + 1


def test_the_border_is_solid() -> None:
    level = build_level(11, 11, 50, 42)
    for x in range(level.cols):
        assert level.is_wall(x, 0)
        assert level.is_wall(x, level.rows - 1)
    for y in range(level.rows):
        assert level.is_wall(0, y)
        assert level.is_wall(level.cols - 1, y)


def test_out_of_bounds_counts_as_a_wall() -> None:
    level = build_level(9, 9, 20, 42)
    assert level.is_wall(-1, 0)
    assert level.is_wall(0, -1)
    assert level.is_wall(level.cols, 0)
    assert level.is_wall(0, level.rows)


def test_the_same_seed_gives_the_same_maze() -> None:
    first = build_level(13, 13, 50, 4242)
    second = build_level(13, 13, 50, 4242)
    assert first.tiles == second.tiles
    assert first.pacgums == second.pacgums
    assert first.player_spawn == second.player_spawn


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("seed", SEEDS)
def test_spawns_are_on_corridors(size: int, seed: int) -> None:
    level = build_level(size, size, 200, seed)
    assert not level.is_wall(*level.player_spawn)
    assert len(level.ghost_spawns) == 4
    for spawn in level.ghost_spawns:
        assert not level.is_wall(*spawn)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("seed", SEEDS)
def test_everything_is_reachable_from_the_player(size: int, seed: int) -> None:
    level = build_level(size, size, 200, seed)
    area = reachable(level, level.player_spawn)
    assert level.pacgums <= area
    assert level.super_pacgums <= area
    assert set(level.ghost_spawns) <= area


@pytest.mark.parametrize("size", SIZES)
def test_there_are_four_super_pacgums_near_the_corners(size: int) -> None:
    level = build_level(size, size, 200, 42)
    assert len(level.super_pacgums) == 4
    corners = ((0, 0), (level.cols - 1, 0),
               (0, level.rows - 1), (level.cols - 1, level.rows - 1))
    for gum in level.super_pacgums:
        closest = min(
            (gum[0] - cx) ** 2 + (gum[1] - cy) ** 2 for cx, cy in corners
        )
        assert closest <= 5 ** 2


def test_collectibles_never_overlap_the_player_spawn() -> None:
    level = build_level(15, 15, 500, 42)
    assert level.player_spawn not in level.pacgums
    assert level.player_spawn not in level.super_pacgums
    assert not level.pacgums & level.super_pacgums


def test_pacgum_count_is_honoured() -> None:
    level = build_level(15, 15, 25, 42)
    assert len(level.pacgums) == 25


def test_pacgum_count_is_clamped_to_the_corridors() -> None:
    level = build_level(7, 7, 100_000, 42)
    corridors = sum(
        1
        for row in level.tiles
        for tile in row
        if tile is Tile.CORRIDOR
    )
    assert len(level.pacgums) == corridors - 1 - len(level.super_pacgums)


def test_missing_generator_is_reported_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(name: str) -> None:
        raise ImportError("no module named mazegenerator")

    monkeypatch.setattr(importlib, "import_module", explode)
    with pytest.raises(MazeError, match="not installed"):
        build_level(9, 9, 10, 1)
