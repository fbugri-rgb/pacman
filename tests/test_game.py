"""Tests for movement, scoring, lives and cheats."""

from __future__ import annotations

import random

import pytest

from pacman.config import GameConfig, LevelConfig, parse_config
from pacman.constants import Direction, GhostState, Tile
from pacman.entities import Actor, Ghost, Player, collides
from pacman.game import Game, GameStatus
from pacman.maze import Level, Position

pytest.importorskip("mazegenerator")

# A tiny hand-made board: a plus-shaped set of corridors inside a ring of
# walls, so movement can be checked without invoking the generator.
#   #####
#   ##.##
#   #...#
#   ##.##
#   #####
PLUS = (
    "#####",
    "##.##",
    "#...#",
    "##.##",
    "#####",
)


def make_level(rows: tuple[str, ...] = PLUS) -> Level:
    """Build a level from an ASCII drawing."""
    tiles = tuple(
        tuple(Tile.WALL if char == "#" else Tile.CORRIDOR for char in row)
        for row in rows
    )
    return Level(
        tiles=tiles,
        player_spawn=(2, 2),
        ghost_spawns=((2, 1), (1, 2), (3, 2), (2, 3)),
        pacgums=frozenset({(2, 1)}),
        super_pacgums=frozenset({(1, 2)}),
        seed=1,
    )


def small_config(**overrides: object) -> GameConfig:
    """Build a configuration with tiny, fast levels."""
    levels = tuple(
        LevelConfig(7, 7, 12, 30, 3.0) for _ in range(3)
    )
    base: dict[str, object] = {
        "levels": levels,
        "lives": 3,
        "highscore_filename": "unused.json",
    }
    base.update(overrides)
    return GameConfig(**base)  # type: ignore[arg-type]


def test_actor_interpolates_between_tiles() -> None:
    level = make_level()
    actor = Actor((2, 2), Direction.UP, 1.0)
    actor.update(0.5, level, lambda _: Direction.UP)
    assert actor.position == pytest.approx((2.0, 1.5))


def test_actor_crosses_exactly_one_tile_per_second() -> None:
    level = make_level()
    actor = Actor((2, 2), Direction.UP, 1.0)
    assert actor.update(1.0, level, lambda _: Direction.UP) == 1
    assert actor.tile == (2, 1)


def test_actor_stops_against_a_wall() -> None:
    level = make_level()
    actor = Actor((2, 1), Direction.UP, 10.0)
    actor.update(1.0, level, lambda _: Direction.UP)
    assert actor.tile == (2, 1)
    assert actor.progress == 0.0


def test_actor_stands_still_when_no_direction_is_chosen() -> None:
    level = make_level()
    actor = Actor((2, 2), Direction.UP, 10.0)
    actor.update(1.0, level, lambda _: None)
    assert actor.position == (2.0, 2.0)


def test_open_directions_lists_only_corridors() -> None:
    level = make_level()
    actor = Actor((2, 1), Direction.UP, 1.0)
    assert actor.open_directions(level) == [Direction.DOWN]


def test_player_waits_for_the_first_key() -> None:
    level = make_level()
    player = Player((2, 2), 6.0)
    player.update(1.0, level, player.picker(level))
    assert player.tile == (2, 2)


def test_player_moves_once_steered() -> None:
    level = make_level()
    player = Player((2, 2), 1.0)
    player.steer(Direction.UP, level)
    player.update(1.0, level, player.picker(level))
    assert player.tile == (2, 1)


def test_player_reverses_instantly() -> None:
    level = make_level()
    player = Player((2, 2), 1.0)
    player.steer(Direction.UP, level)
    player.update(0.25, level, player.picker(level))
    player.steer(Direction.DOWN, level)
    assert player.direction is Direction.DOWN
    assert player.position == pytest.approx((2.0, 2.0 - 0.25))


def test_player_buffers_an_impossible_turn() -> None:
    level = make_level()
    player = Player((2, 3), 1.0)
    player.steer(Direction.UP, level)
    player.steer(Direction.LEFT, level)
    player.update(1.0, level, player.picker(level))
    assert player.tile == (2, 2)
    assert player.desired is Direction.LEFT


def test_ghost_walks_towards_the_player() -> None:
    level = make_level()
    player = Player((2, 3), 1.0)
    ghost = Ghost(0, (2, 1), 1.0, random.Random(0))
    ghost.update(1.0, level, ghost.picker(level, player, ghost, False))
    assert ghost.tile == (2, 2)


def test_frightened_ghost_runs_away() -> None:
    level = make_level()
    player = Player((2, 1), 1.0)
    ghost = Ghost(0, (2, 2), 1.0, random.Random(0))
    ghost.direction = Direction.DOWN
    ghost.frighten()
    ghost.update(1.0, level, ghost.picker(level, player, ghost, False))
    assert ghost.tile == (2, 3)


def test_a_ghost_does_not_turn_back_on_itself() -> None:
    level = make_level()
    player = Player((2, 1), 1.0)
    ghost = Ghost(0, (2, 2), 1.0, random.Random(0))
    ghost.frighten()
    ghost.update(1.0, level, ghost.picker(level, player, ghost, False))
    assert ghost.tile in {(1, 2), (3, 2)}


def test_an_eaten_ghost_stays_away_until_its_timer_runs_out() -> None:
    ghost = Ghost(0, (2, 1), 1.0, random.Random(0))
    ghost.tile = (2, 3)
    ghost.eaten(2.0)
    assert ghost.state is GhostState.EATEN
    assert not ghost.active
    ghost.tick_respawn(1.0)
    assert not ghost.active


def test_a_respawned_ghost_hunts_again_from_its_corner() -> None:
    ghost = Ghost(0, (2, 1), 1.0, random.Random(0))
    ghost.tile = (2, 3)
    ghost.eaten(2.0)
    ghost.tick_respawn(2.5)
    assert ghost.state is GhostState.CHASE
    assert ghost.tile == (2, 1)


def test_an_eaten_ghost_cannot_be_frightened() -> None:
    ghost = Ghost(0, (2, 1), 1.0, random.Random(0))
    ghost.eaten(5.0)
    ghost.frighten()
    assert ghost.state is GhostState.EATEN


def test_collision_ignores_eaten_ghosts() -> None:
    player = Player((2, 2), 1.0)
    ghost = Ghost(0, (2, 2), 1.0, random.Random(0))
    assert collides(player, ghost)
    ghost.eaten(5.0)
    assert not collides(player, ghost)


def run(game: Game, seconds: float) -> None:
    """Advance a game by ``seconds`` at sixty frames per second."""
    for _ in range(int(seconds * 60)):
        game.update(1 / 60)


def test_a_new_game_starts_on_the_first_level() -> None:
    game = Game(small_config())
    assert game.level_index == 0
    assert game.lives == 3
    assert game.score == 0
    assert game.status is GameStatus.RUNNING


def test_the_first_level_uses_the_configured_seed() -> None:
    game = Game(small_config(seed=1234))
    assert game.level.seed == 1234


def test_eating_a_pacgum_scores() -> None:
    game = Game(small_config(points_per_pacgum=7))
    target = next(iter(game.pacgums))
    game.player.tile = target
    game.player.next_tile = target
    game._collect()
    assert game.score == 7
    assert target not in game.pacgums


def test_eating_a_super_pacgum_frightens_the_ghosts() -> None:
    game = Game(small_config(points_per_super_pacgum=11))
    target = next(iter(game.super_pacgums))
    game.player.tile = target
    game.player.next_tile = target
    game._collect()
    assert game.score == 11
    assert game.frightened_timer > 0.0
    assert all(ghost.edible for ghost in game.ghosts)


def test_eating_a_ghost_scores_and_removes_it() -> None:
    game = Game(small_config(points_per_ghost=200))
    ghost = game.ghosts[0]
    ghost.frighten()
    ghost.tile = game.player.tile
    ghost.next_tile = game.player.tile
    game._resolve_contacts()
    assert game.score == 200
    assert ghost.state is GhostState.EATEN


def test_touching_a_ghost_costs_a_life() -> None:
    game = Game(small_config())
    ghost = game.ghosts[0]
    ghost.tile = game.player.tile
    ghost.next_tile = game.player.tile
    game._resolve_contacts()
    assert game.lives == 2
    assert game.player.tile == game.level.player_spawn


def test_the_last_life_ends_the_game() -> None:
    game = Game(small_config(lives=1))
    ghost = game.ghosts[0]
    ghost.tile = game.player.tile
    ghost.next_tile = game.player.tile
    game._resolve_contacts()
    assert game.lives == 0
    assert game.status is GameStatus.GAME_OVER


def test_invincibility_protects_the_player() -> None:
    game = Game(small_config())
    game.toggle_invincible()
    ghost = game.ghosts[0]
    ghost.tile = game.player.tile
    ghost.next_tile = game.player.tile
    game._resolve_contacts()
    assert game.lives == 3
    assert game.cheats.used


def test_running_out_of_time_restarts_the_level() -> None:
    game = Game(small_config())
    game.pacgums.clear()
    game.time_left = 0.001
    run(game, 3.0)
    assert game.lives == 2
    assert game.pacgums == set(game.level.pacgums)
    assert game.time_left == pytest.approx(game.level_config.max_time)


def test_clearing_every_pacgum_clears_the_level() -> None:
    game = Game(small_config())
    game.pacgums.clear()
    game.super_pacgums.clear()
    run(game, 2.0)
    assert game.status is GameStatus.LEVEL_CLEARED


def test_next_level_keeps_score_and_lives() -> None:
    game = Game(small_config())
    game.score = 500
    game.lives = 2
    assert game.next_level()
    assert game.level_index == 1
    assert game.score == 500
    assert game.lives == 2
    assert game.status is GameStatus.RUNNING


def test_finishing_the_last_level_wins_the_game() -> None:
    game = Game(small_config())
    assert game.next_level()
    assert game.next_level()
    assert not game.next_level()
    assert game.status is GameStatus.VICTORY


def test_frozen_ghosts_do_not_move() -> None:
    game = Game(small_config())
    game.toggle_frozen()
    before = [ghost.position for ghost in game.ghosts]
    run(game, 3.0)
    assert [ghost.position for ghost in game.ghosts] == before


def test_skip_level_clears_the_board() -> None:
    game = Game(small_config())
    game.skip_level()
    assert game.status is GameStatus.LEVEL_CLEARED
    assert game.remaining_pacgums == 0


def test_grant_life_adds_one() -> None:
    game = Game(small_config())
    game.grant_life()
    assert game.lives == 4


def test_speed_cheat_speeds_the_player_up() -> None:
    game = Game(small_config())
    normal = game.player_speed
    game.toggle_fast()
    assert game.player_speed > normal


def test_end_run_goes_to_game_over() -> None:
    game = Game(small_config())
    game.end_run()
    assert game.status is GameStatus.GAME_OVER


def test_the_score_never_decreases() -> None:
    game = Game(parse_config("{}"))
    game.cheats.invincible = True
    generator = random.Random(7)
    best = 0
    for _ in range(60 * 120):
        if not game.player.moving:
            options = game.player.open_directions(game.level)
            if options:
                game.steer(generator.choice(options))
        game.update(1 / 60)
        assert game.score >= best
        best = game.score
        if game.status is not GameStatus.RUNNING:
            break


def test_the_player_never_walks_through_a_wall() -> None:
    game = Game(parse_config("{}"))
    generator = random.Random(3)
    for _ in range(60 * 60):
        if not game.player.moving:
            options = game.player.open_directions(game.level)
            if options:
                game.steer(generator.choice(options))
        game.update(1 / 60)
        assert not game.level.is_wall(*game.player.tile)
        assert not game.level.is_wall(*game.player.next_tile)
        for ghost in game.ghosts:
            assert not game.level.is_wall(*ghost.tile)
            assert not game.level.is_wall(*ghost.next_tile)
        if game.status is not GameStatus.RUNNING:
            break


def test_position_stays_inside_the_maze() -> None:
    game = Game(small_config())
    positions: list[Position] = []
    run(game, 5.0)
    for ghost in game.ghosts:
        positions.append(ghost.tile)
    for x, y in positions:
        assert 0 <= x < game.level.cols
        assert 0 <= y < game.level.rows
