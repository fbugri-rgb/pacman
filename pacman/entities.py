"""The player and the ghosts.

Actors live on the tile grid but move continuously between tiles.  Each
one remembers the tile it is leaving, the tile it is entering and how far
along it is, which keeps movement smooth while making every decision
happen exactly on a tile boundary, as in the arcade original.
"""

from __future__ import annotations

import random
from typing import Callable, Optional

from .constants import Direction, GhostState
from .maze import Level, Position

# How far ahead of the player Pinky aims, in tiles.
PINKY_LOOKAHEAD = 4
# Pivot used to mirror Blinky's tile when computing Inky's target.
INKY_PIVOT = 2
# Below this distance Clyde stops chasing and retreats to his corner.
CLYDE_SHY_DISTANCE = 8
# Tiles closer than this to the player count as a collision.
CATCH_DISTANCE = 0.6

DirectionPicker = Callable[["Actor"], Optional[Direction]]


class Actor:
    """An entity moving from tile to tile at a constant speed.

    Attributes:
        tile: The tile the actor is leaving.
        next_tile: The tile the actor is entering.
        progress: How far along the current step, in ``[0, 1)``.
        direction: The direction currently faced.
        speed: Movement speed in tiles per second.
    """

    def __init__(
        self, spawn: Position, direction: Direction, speed: float
    ) -> None:
        """Create an actor standing still on ``spawn``.

        Args:
            spawn: Starting tile.
            direction: Direction faced on spawn.
            speed: Movement speed in tiles per second.
        """
        self.tile: Position = spawn
        self.next_tile: Position = spawn
        self.progress: float = 0.0
        self.direction: Direction = direction
        self.speed: float = speed

    @property
    def position(self) -> tuple[float, float]:
        """Return the interpolated position, in tile units."""
        x, y = self.tile
        nx, ny = self.next_tile
        return (
            x + (nx - x) * self.progress,
            y + (ny - y) * self.progress,
        )

    @property
    def moving(self) -> bool:
        """Tell whether the actor is between two tiles."""
        return self.tile != self.next_tile

    def reset(self, spawn: Position, direction: Direction) -> None:
        """Teleport the actor back to ``spawn``, standing still.

        Args:
            spawn: Tile to return to.
            direction: Direction to face.
        """
        self.tile = spawn
        self.next_tile = spawn
        self.progress = 0.0
        self.direction = direction

    def reverse(self) -> None:
        """Turn around without waiting for the next tile boundary."""
        self.tile, self.next_tile = self.next_tile, self.tile
        self.progress = 1.0 - self.progress
        self.direction = self.direction.opposite

    def update(self, delta: float, level: Level, pick: DirectionPicker) -> int:
        """Advance the actor by ``delta`` seconds.

        ``pick`` is consulted every time the actor reaches a tile centre,
        which is the only moment a direction may change.

        Args:
            delta: Elapsed time in seconds.
            level: The maze, used for wall tests.
            pick: Chooses the next direction, or ``None`` to stand still.

        Returns:
            How many tile boundaries were crossed.
        """
        crossed = 0
        remaining = max(delta, 0.0)
        while remaining > 0.0:
            if not self.moving and not self._start_step(level, pick):
                break
            self.progress += self.speed * remaining
            if self.progress < 1.0:
                break
            remaining = (self.progress - 1.0) / self.speed
            self.tile = self.next_tile
            self.progress = 0.0
            crossed += 1
        return crossed

    def _start_step(self, level: Level, pick: DirectionPicker) -> bool:
        """Try to leave the current tile.

        Args:
            level: The maze, used for wall tests.
            pick: Chooses the next direction.

        Returns:
            ``True`` if a step towards a free tile was started.
        """
        direction = pick(self)
        if direction is None:
            return False
        target = self.step_target(direction)
        if level.is_wall(*target):
            return False
        self.direction = direction
        self.next_tile = target
        return True

    def step_target(self, direction: Direction) -> Position:
        """Return the tile one step away in ``direction``.

        Args:
            direction: The direction to look towards.

        Returns:
            The neighbouring tile coordinates.
        """
        dx, dy = direction.delta
        return self.tile[0] + dx, self.tile[1] + dy

    def open_directions(self, level: Level) -> list[Direction]:
        """List the directions that do not run into a wall.

        Args:
            level: The maze, used for wall tests.

        Returns:
            Every walkable direction from the current tile.
        """
        return [
            direction
            for direction in Direction
            if not level.is_wall(*self.step_target(direction))
        ]


class Player(Actor):
    """Pac-Man himself.

    Attributes:
        desired: The direction requested by the player, applied as soon as
            the maze allows it.
        started: Whether the player has taken control yet; Pac-Man waits
            on his spawn tile until the first key press.
    """

    def __init__(self, spawn: Position, speed: float) -> None:
        """Create the player on ``spawn``.

        Args:
            spawn: Starting tile.
            speed: Movement speed in tiles per second.
        """
        super().__init__(spawn, Direction.LEFT, speed)
        self.desired: Direction | None = None
        self.started: bool = False

    def steer(self, direction: Direction, level: Level) -> None:
        """Register a direction change requested by the player.

        A half-turn is applied immediately, which is what makes the
        controls feel responsive; any other turn waits for the next tile.

        Args:
            direction: The direction the player asked for.
            level: The maze, used for wall tests.
        """
        self.started = True
        self.desired = direction
        if self.moving and direction is self.direction.opposite:
            self.reverse()
            self.desired = None
            return
        if not self.moving and not level.is_wall(*self.step_target(direction)):
            self.direction = direction

    def picker(self, level: Level) -> DirectionPicker:
        """Build the direction chooser used by :meth:`Actor.update`.

        Args:
            level: The maze, used for wall tests.

        Returns:
            A callable that prefers the requested direction and otherwise
            keeps going straight.
        """
        def pick(actor: Actor) -> Direction | None:
            if not self.started:
                return None
            wanted = self.desired
            if wanted is not None:
                if not level.is_wall(*actor.step_target(wanted)):
                    self.desired = None
                    return wanted
            if not level.is_wall(*actor.step_target(actor.direction)):
                return actor.direction
            return None

        return pick

    def reset(self, spawn: Position, direction: Direction) -> None:
        """Return to ``spawn`` and forget any buffered input.

        Args:
            spawn: Tile to return to.
            direction: Direction to face.
        """
        super().reset(spawn, direction)
        self.desired = None
        self.started = False


class Ghost(Actor):
    """One of the four ghosts, with its own way of hunting the player.

    Attributes:
        index: Which ghost this is, from 0 (Blinky) to 3 (Clyde).
        home: The corner the ghost starts in and retreats to.
        state: Whether the ghost is hunting, edible or eaten.
        respawn_timer: Seconds left before an eaten ghost comes back.
    """

    def __init__(
        self, index: int, home: Position, speed: float, rng: random.Random
    ) -> None:
        """Create a ghost in its corner.

        Args:
            index: Ghost number, from 0 to 3.
            home: The corner tile the ghost belongs to.
            speed: Movement speed in tiles per second.
            rng: Random source used to break ties between directions.
        """
        super().__init__(home, Direction.UP, speed)
        self.index: int = index
        self.home: Position = home
        self.state: GhostState = GhostState.CHASE
        self.respawn_timer: float = 0.0
        self._rng = rng

    @property
    def edible(self) -> bool:
        """Tell whether the player may eat this ghost right now."""
        return self.state is GhostState.FRIGHTENED

    @property
    def active(self) -> bool:
        """Tell whether the ghost is currently on the board."""
        return self.state is not GhostState.EATEN

    def frighten(self) -> None:
        """Make the ghost edible and send it running the other way."""
        if self.state is GhostState.EATEN:
            return
        self.state = GhostState.FRIGHTENED
        if self.moving:
            self.reverse()

    def unfrighten(self) -> None:
        """Return an edible ghost to its hunting state."""
        if self.state is GhostState.FRIGHTENED:
            self.state = GhostState.CHASE

    def eaten(self, delay: float) -> None:
        """Remove the ghost from the board for ``delay`` seconds.

        Args:
            delay: How long before the ghost reappears in its corner.
        """
        self.state = GhostState.EATEN
        self.respawn_timer = delay
        self.reset(self.home, Direction.UP)

    def tick_respawn(self, delta: float) -> None:
        """Count down the respawn delay of an eaten ghost.

        Args:
            delta: Elapsed time in seconds.
        """
        if self.state is not GhostState.EATEN:
            return
        self.respawn_timer -= delta
        if self.respawn_timer <= 0.0:
            self.respawn_timer = 0.0
            self.state = GhostState.CHASE
            self.reset(self.home, Direction.UP)

    def target(
        self, player: Player, blinky: "Ghost", scatter: bool
    ) -> Position:
        """Return the tile this ghost is currently heading for.

        Each ghost keeps the personality of the arcade original: Blinky
        goes straight for the player, Pinky aims ahead of him, Inky uses
        Blinky's position as a lever, and Clyde backs off when he gets
        close.

        Args:
            player: The player being hunted.
            blinky: The red ghost, needed for Inky's target.
            scatter: Whether ghosts are in their periodic retreat phase.

        Returns:
            The tile the ghost tries to reach.
        """
        if self.state is GhostState.FRIGHTENED or scatter:
            return self.home
        px, py = player.tile
        if self.index == 0:
            return px, py
        dx, dy = player.direction.delta
        if self.index == 1:
            return px + dx * PINKY_LOOKAHEAD, py + dy * PINKY_LOOKAHEAD
        if self.index == 2:
            pivot_x = px + dx * INKY_PIVOT
            pivot_y = py + dy * INKY_PIVOT
            return 2 * pivot_x - blinky.tile[0], 2 * pivot_y - blinky.tile[1]
        distance = abs(px - self.tile[0]) + abs(py - self.tile[1])
        return (px, py) if distance > CLYDE_SHY_DISTANCE else self.home

    def picker(
        self, level: Level, player: Player, blinky: "Ghost", scatter: bool
    ) -> DirectionPicker:
        """Build the direction chooser used by :meth:`Actor.update`.

        The ghost heads for its target tile and never turns back on itself
        unless the corridor leaves it no other option.  An edible ghost
        inverts the rule and maximises its distance from the player.

        Args:
            level: The maze, used for wall tests.
            player: The player being hunted or fled.
            blinky: The red ghost, needed for Inky's target.
            scatter: Whether ghosts are in their periodic retreat phase.

        Returns:
            A callable choosing the next direction.
        """
        target = self.target(player, blinky, scatter)
        fleeing = self.state is GhostState.FRIGHTENED

        def cost(direction: Direction) -> float:
            dx, dy = direction.delta
            x = self.tile[0] + dx
            y = self.tile[1] + dy
            squared = (x - target[0]) ** 2 + (y - target[1]) ** 2
            if fleeing:
                px, py = player.tile
                squared = -((x - px) ** 2 + (y - py) ** 2)
            return squared + self._rng.random() * 0.1

        def pick(actor: Actor) -> Direction | None:
            options = actor.open_directions(level)
            if not options:
                return None
            forward = [
                direction
                for direction in options
                if direction is not actor.direction.opposite
            ]
            return min(forward or options, key=cost)

        return pick


def collides(player: Player, ghost: Ghost) -> bool:
    """Tell whether the player and a ghost are touching.

    Args:
        player: The player.
        ghost: The ghost to test against.

    Returns:
        ``True`` if they are close enough to interact.
    """
    if not ghost.active:
        return False
    px, py = player.position
    gx, gy = ghost.position
    return abs(px - gx) < CATCH_DISTANCE and abs(py - gy) < CATCH_DISTANCE
