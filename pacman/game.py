"""Rules of a Pac-Man run: levels, scoring, lives and cheats.

This module owns the whole simulation and knows nothing about drawing or
input devices, which keeps it testable without opening a window.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Final

from .config import GameConfig, LevelConfig, MAX_SEED
from .constants import Direction, GhostState
from .entities import Ghost, Player, collides
from .maze import Level, build_level

# Length of the "get ready" freeze at the start of a life, in seconds.
READY_PAUSE: Final[float] = 1.5
# How long an on-screen notice stays visible, in seconds.
NOTICE_DURATION: Final[float] = 2.0
# Ghosts alternate between hunting the player and retreating to their
# corner, which keeps a level solvable without making the ghosts dumb.
SCATTER_DURATION: Final[float] = 7.0
CHASE_DURATION: Final[float] = 20.0
# Speed multiplier granted by the speed cheat.
CHEAT_SPEED_FACTOR: Final[float] = 1.8


class GameStatus(Enum):
    """What the run is currently waiting for."""

    RUNNING = "running"
    LEVEL_CLEARED = "level_cleared"
    GAME_OVER = "game_over"
    VICTORY = "victory"


@dataclass
class Cheats:
    """State of the cheat menu.

    Attributes:
        invincible: Ghosts cannot take a life.
        frozen: Ghosts stand still.
        fast: The player moves faster than normal.
        used: Whether any cheat was ever enabled during this run.
    """

    invincible: bool = False
    frozen: bool = False
    fast: bool = False
    used: bool = False

    @property
    def any_active(self) -> bool:
        """Tell whether at least one cheat is currently on."""
        return self.invincible or self.frozen or self.fast

    def summary(self) -> str:
        """Return a short description of the active cheats."""
        labels = []
        if self.invincible:
            labels.append("INVINCIBLE")
        if self.frozen:
            labels.append("GHOSTS FROZEN")
        if self.fast:
            labels.append("SPEED")
        return " / ".join(labels)


class Game:
    """A single run, from the first level to the game over screen.

    Attributes:
        config: The validated configuration driving the run.
        score: Points collected so far; it never decreases.
        lives: Lives left, including the one being played.
        level_index: Zero based index of the current level.
        status: Whether the run is running, cleared, lost or won.
        cheats: State of the cheat menu.
        notice: Short message to flash over the maze.
    """

    def __init__(self, config: GameConfig) -> None:
        """Start a run on the first level.

        Args:
            config: A validated configuration.

        Raises:
            MazeError: If the first maze cannot be generated.
        """
        self.config: GameConfig = config
        self.score: int = 0
        self.lives: int = config.lives
        self.level_index: int = 0
        self.status: GameStatus = GameStatus.RUNNING
        self.cheats: Cheats = Cheats()
        self.notice: str = ""
        self._notice_timer: float = 0.0
        self._rng = random.Random()
        self.level: Level = self._generate(0)
        self.pacgums: set[tuple[int, int]] = set()
        self.super_pacgums: set[tuple[int, int]] = set()
        self.player: Player = Player(
            self.level.player_spawn, config.player_speed
        )
        self.ghosts: list[Ghost] = []
        self.time_left: float = 0.0
        self.frightened_timer: float = 0.0
        self._freeze_timer: float = 0.0
        self._phase_timer: float = SCATTER_DURATION
        self.scatter: bool = True
        self._install_level()

    @property
    def level_config(self) -> LevelConfig:
        """Return the configuration of the current level."""
        return self.config.levels[self.level_index]

    @property
    def level_count(self) -> int:
        """Return how many levels the run contains."""
        return len(self.config.levels)

    @property
    def remaining_pacgums(self) -> int:
        """Return how many collectibles are left on the board."""
        return len(self.pacgums) + len(self.super_pacgums)

    @property
    def player_speed(self) -> float:
        """Return the player speed, cheats included."""
        speed = self.config.player_speed
        return speed * CHEAT_SPEED_FACTOR if self.cheats.fast else speed

    def _generate(self, index: int) -> Level:
        """Build the maze of level ``index``.

        The first level always uses the configured seed so that it is
        reproducible; every later level gets a random one.

        Args:
            index: Zero based level index.

        Returns:
            The generated level.

        Raises:
            MazeError: If the generator failed.
        """
        settings = self.config.levels[index]
        seed = (
            self.config.seed
            if index == 0
            else self._rng.randrange(1, MAX_SEED)
        )
        return build_level(
            settings.width, settings.height, settings.pacgum, seed
        )

    def _install_level(self) -> None:
        """Reset every per-level piece of state from :attr:`level`."""
        self.pacgums = set(self.level.pacgums)
        self.super_pacgums = set(self.level.super_pacgums)
        self.player = Player(self.level.player_spawn, self.player_speed)
        self.ghosts = [
            Ghost(index, spawn, self.level_config.ghost_speed, self._rng)
            for index, spawn in enumerate(self.level.ghost_spawns)
        ]
        self.time_left = float(self.level_config.max_time)
        self.frightened_timer = 0.0
        self._freeze_timer = READY_PAUSE
        self._phase_timer = SCATTER_DURATION
        self.scatter = True
        self.flash(f"LEVEL {self.level_index + 1}")

    def flash(self, message: str) -> None:
        """Show a short message over the maze.

        Args:
            message: The text to display.
        """
        self.notice = message
        self._notice_timer = NOTICE_DURATION

    def next_level(self) -> bool:
        """Move on to the next level, or win the game.

        Returns:
            ``True`` if a new level was loaded, ``False`` if the run is won.

        Raises:
            MazeError: If the next maze cannot be generated.
        """
        if self.level_index + 1 >= self.level_count:
            self.status = GameStatus.VICTORY
            return False
        self.level_index += 1
        self.level = self._generate(self.level_index)
        self.status = GameStatus.RUNNING
        self._install_level()
        return True

    def steer(self, direction: Direction) -> None:
        """Ask the player to change direction.

        Args:
            direction: The direction requested by the human.
        """
        if self.status is GameStatus.RUNNING:
            self.player.steer(direction, self.level)

    def update(self, delta: float) -> None:
        """Advance the simulation by ``delta`` seconds.

        Args:
            delta: Elapsed time in seconds, already clamped by the caller.
        """
        if self.status is not GameStatus.RUNNING:
            return
        self._tick_notice(delta)
        for ghost in self.ghosts:
            ghost.tick_respawn(delta)
        if self._freeze_timer > 0.0:
            self._freeze_timer -= delta
            return
        self._tick_timers(delta)
        if self.status is not GameStatus.RUNNING:
            return
        self.player.speed = self.player_speed
        self.player.update(delta, self.level, self.player.picker(self.level))
        self._collect()
        if not self.cheats.frozen:
            self._move_ghosts(delta)
        self._resolve_contacts()
        if self.remaining_pacgums == 0:
            self.status = GameStatus.LEVEL_CLEARED

    def _tick_notice(self, delta: float) -> None:
        """Count the on-screen notice down.

        Args:
            delta: Elapsed time in seconds.
        """
        if self._notice_timer > 0.0:
            self._notice_timer -= delta
            if self._notice_timer <= 0.0:
                self.notice = ""

    def _tick_timers(self, delta: float) -> None:
        """Advance the level clock, the power-up and the ghost phases.

        Args:
            delta: Elapsed time in seconds.
        """
        self.time_left -= delta
        if self.time_left <= 0.0:
            self.time_left = 0.0
            self._lose_life("TIME UP!", restart=True)
            return
        if self.frightened_timer > 0.0:
            self.frightened_timer -= delta
            if self.frightened_timer <= 0.0:
                self.frightened_timer = 0.0
                for ghost in self.ghosts:
                    ghost.unfrighten()
            return
        self._phase_timer -= delta
        if self._phase_timer <= 0.0:
            self.scatter = not self.scatter
            self._phase_timer = (
                SCATTER_DURATION if self.scatter else CHASE_DURATION
            )

    def _move_ghosts(self, delta: float) -> None:
        """Let every active ghost take its step.

        Args:
            delta: Elapsed time in seconds.
        """
        blinky = self.ghosts[0]
        for ghost in self.ghosts:
            if not ghost.active:
                continue
            ghost.speed = self.level_config.ghost_speed
            ghost.update(
                delta,
                self.level,
                ghost.picker(self.level, self.player, blinky, self.scatter),
            )

    def _collect(self) -> None:
        """Pick up whatever sits on the player's tile."""
        tile = self.player.tile
        if tile in self.pacgums:
            self.pacgums.discard(tile)
            self.score += self.config.points_per_pacgum
        elif tile in self.super_pacgums:
            self.super_pacgums.discard(tile)
            self.score += self.config.points_per_super_pacgum
            self.frightened_timer = self.config.super_pacgum_duration
            for ghost in self.ghosts:
                ghost.frighten()
            self.flash("GHOSTS ON THE MENU!")

    def _resolve_contacts(self) -> None:
        """Handle the player running into a ghost."""
        for ghost in self.ghosts:
            if not collides(self.player, ghost):
                continue
            if ghost.edible:
                ghost.eaten(self.config.ghost_respawn_delay)
                self.score += self.config.points_per_ghost
                self.flash(f"+{self.config.points_per_ghost}")
                continue
            if self.cheats.invincible:
                continue
            self._lose_life("OUCH!", restart=False)
            return

    def _lose_life(self, reason: str, restart: bool) -> None:
        """Take a life away and set the board back up.

        Args:
            reason: Message flashed to explain what happened.
            restart: Whether the whole level restarts, which also puts
                every collectible back.
        """
        self.lives -= 1
        if self.lives <= 0:
            self.lives = 0
            self.status = GameStatus.GAME_OVER
            return
        self.flash(reason)
        if restart:
            self.pacgums = set(self.level.pacgums)
            self.super_pacgums = set(self.level.super_pacgums)
            self.time_left = float(self.level_config.max_time)
        self.player.reset(self.level.player_spawn, Direction.LEFT)
        self.frightened_timer = 0.0
        for ghost in self.ghosts:
            ghost.state = GhostState.CHASE
            ghost.respawn_timer = 0.0
            ghost.reset(ghost.home, Direction.UP)
        self._freeze_timer = READY_PAUSE
        self.scatter = True
        self._phase_timer = SCATTER_DURATION

    def toggle_invincible(self) -> None:
        """Turn the invincibility cheat on or off."""
        self.cheats.invincible = not self.cheats.invincible
        self.cheats.used = True
        self.flash(
            "INVINCIBLE ON" if self.cheats.invincible else "INVINCIBLE OFF"
        )

    def toggle_frozen(self) -> None:
        """Turn the ghost freeze cheat on or off."""
        self.cheats.frozen = not self.cheats.frozen
        self.cheats.used = True
        self.flash("GHOSTS FROZEN" if self.cheats.frozen else "GHOSTS FREED")

    def toggle_fast(self) -> None:
        """Turn the extra speed cheat on or off."""
        self.cheats.fast = not self.cheats.fast
        self.cheats.used = True
        self.flash("SPEED ON" if self.cheats.fast else "SPEED OFF")

    def grant_life(self) -> None:
        """Give the player one more life."""
        self.cheats.used = True
        self.lives += 1
        self.flash(f"LIVES: {self.lives}")

    def skip_level(self) -> None:
        """Clear the current level immediately."""
        self.cheats.used = True
        self.pacgums.clear()
        self.super_pacgums.clear()
        self.status = GameStatus.LEVEL_CLEARED

    def end_run(self) -> None:
        """Give up the run and go straight to the game over screen."""
        self.lives = 0
        self.status = GameStatus.GAME_OVER
