"""Every screen the player sees.

The functions here only read state and call :mod:`pacman.render`; they
never mutate the game, which keeps the drawing code easy to reason about.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Sequence

from .constants import (
    COLOR_BACKGROUND,
    COLOR_DANGER,
    COLOR_FRIGHTENED,
    COLOR_FRIGHTENED_BLINK,
    COLOR_HIGHLIGHT,
    COLOR_PACGUM,
    COLOR_PLAYER,
    COLOR_SUCCESS,
    COLOR_SUPER_PACGUM,
    COLOR_TEXT,
    COLOR_TEXT_DIM,
    COLOR_WALL,
    COLOR_WALL_EDGE,
    Color,
    Direction,
    GHOST_COLORS,
    GHOST_NAMES,
    HUD_HEIGHT,
    Tile,
)
from .entities import Ghost, Player
from .game import Game
from .highscores import Entry
from .maze import Level
from .render import Align, Display

MENU_ITEMS: Final[tuple[str, ...]] = (
    "Start Game",
    "View Highscores",
    "Instructions",
    "Exit",
)
PAUSE_ITEMS: Final[tuple[str, ...]] = (
    "Resume the game",
    "Return to the main menu",
)
# Ghosts flash white during the last seconds of a super-pacgum.
BLINK_WARNING: Final[float] = 2.0


@dataclass(frozen=True)
class Viewport:
    """Where and how big the maze is drawn.

    Attributes:
        tile: Side of one tile in pixels.
        origin_x: Left edge of the maze in pixels.
        origin_y: Top edge of the maze in pixels.
    """

    tile: int
    origin_x: int
    origin_y: int

    def to_pixels(self, x: float, y: float) -> tuple[int, int]:
        """Convert tile coordinates into the centre of that tile in pixels.

        Args:
            x: Column, possibly fractional.
            y: Row, possibly fractional.

        Returns:
            Pixel coordinates of the tile centre.
        """
        return (
            self.origin_x + int((x + 0.5) * self.tile),
            self.origin_y + int((y + 0.5) * self.tile),
        )


def viewport_for(level: Level, display: Display) -> Viewport:
    """Fit a level inside the window below the HUD.

    The tile size is derived from the maze dimensions, so levels of very
    different sizes all stay fully visible.

    Args:
        level: The level to display.
        display: The window the maze must fit in.

    Returns:
        The computed viewport.
    """
    available_height = display.height - HUD_HEIGHT
    tile = max(min(display.width // level.cols,
                   available_height // level.rows), 2)
    origin_x = (display.width - level.cols * tile) // 2
    origin_y = HUD_HEIGHT + (available_height - level.rows * tile) // 2
    return Viewport(tile, origin_x, origin_y)


def draw_maze(display: Display, level: Level, view: Viewport) -> None:
    """Draw the walls of the maze.

    Args:
        display: Where to draw.
        level: The level whose walls are drawn.
        view: Placement of the maze on screen.
    """
    inset = max(view.tile // 8, 1)
    for y in range(level.rows):
        for x in range(level.cols):
            if level.tiles[y][x] is not Tile.WALL:
                continue
            px = view.origin_x + x * view.tile
            py = view.origin_y + y * view.tile
            display.rect(px, py, view.tile, view.tile, COLOR_WALL_EDGE)
            display.rect(
                px + inset, py + inset,
                view.tile - 2 * inset, view.tile - 2 * inset, COLOR_WALL,
            )


def draw_pacgums(display: Display, game: Game, view: Viewport,
                 elapsed: float) -> None:
    """Draw the remaining pacgums and super-pacgums.

    Args:
        display: Where to draw.
        game: The run holding the collectibles still on the board.
        view: Placement of the maze on screen.
        elapsed: Total running time, used to pulse the super-pacgums.
    """
    small = max(view.tile // 8, 1)
    pulse = 0.75 + 0.25 * math.sin(elapsed * 6.0)
    big = max(int(view.tile * 0.32 * pulse), 2)
    for x, y in game.pacgums:
        display.disc(*view.to_pixels(x, y), small, COLOR_PACGUM)
    for x, y in game.super_pacgums:
        display.disc(*view.to_pixels(x, y), big, COLOR_SUPER_PACGUM)


def draw_player(display: Display, player: Player, view: Viewport,
                elapsed: float) -> None:
    """Draw Pac-Man with an animated mouth.

    Args:
        display: Where to draw.
        player: The player to draw.
        view: Placement of the maze on screen.
        elapsed: Total running time, used to animate the mouth.
    """
    cx, cy = view.to_pixels(*player.position)
    radius = max(int(view.tile * 0.42), 2)
    display.disc(cx, cy, radius, COLOR_PLAYER)
    opening = abs(math.sin(elapsed * 9.0))
    mouth = max(int(radius * opening), 0)
    if mouth <= 0:
        return
    dx, dy = player.direction.delta
    if dx:
        left = cx if dx > 0 else cx - radius
        display.rect(left, cy - mouth // 2, radius, mouth, COLOR_BACKGROUND)
    else:
        top = cy if dy > 0 else cy - radius
        display.rect(cx - mouth // 2, top, mouth, radius, COLOR_BACKGROUND)


def _ghost_color(ghost: Ghost, frightened_timer: float) -> Color:
    """Pick the body colour of a ghost from its state.

    Args:
        ghost: The ghost to colour.
        frightened_timer: Seconds left before ghosts stop being edible.

    Returns:
        The colour to fill the ghost with.
    """
    if not ghost.edible:
        return GHOST_COLORS[ghost.index % len(GHOST_COLORS)]
    if frightened_timer <= BLINK_WARNING and int(frightened_timer * 6) % 2:
        return COLOR_FRIGHTENED_BLINK
    return COLOR_FRIGHTENED


def draw_ghost(display: Display, ghost: Ghost, view: Viewport,
               frightened_timer: float) -> None:
    """Draw one ghost, eyes included.

    Args:
        display: Where to draw.
        ghost: The ghost to draw.
        view: Placement of the maze on screen.
        frightened_timer: Seconds left before ghosts stop being edible.
    """
    if not ghost.active:
        return
    cx, cy = view.to_pixels(*ghost.position)
    radius = max(int(view.tile * 0.42), 2)
    color = _ghost_color(ghost, frightened_timer)
    display.disc(cx, cy - radius // 3, radius, color)
    display.rect(
        cx - radius, cy - radius // 3, 2 * radius, radius + radius // 3, color,
    )
    eye = max(radius // 3, 1)
    pupil = max(eye // 2, 1)
    dx, dy = ghost.direction.delta
    for side in (-1, 1):
        ex = cx + side * eye
        ey = cy - radius // 3
        display.disc(ex, ey, eye, COLOR_TEXT)
        display.disc(
            ex + dx * pupil, ey + dy * pupil, pupil, COLOR_BACKGROUND,
        )


def draw_hud(display: Display, game: Game) -> None:
    """Draw the always-visible score, lives, level and timer.

    Args:
        display: Where to draw.
        game: The run being played.
    """
    display.rect(0, 0, display.width, HUD_HEIGHT, COLOR_BACKGROUND)
    display.rect(0, HUD_HEIGHT - 2, display.width, 2, COLOR_WALL)
    display.text(16, 8, f"SCORE {game.score}", COLOR_TEXT, 30)
    display.text(16, 32, "LIVES", COLOR_TEXT_DIM, 20)
    for index in range(min(game.lives, 8)):
        display.disc(84 + index * 18, 40, 6, COLOR_PLAYER)
    if game.lives > 8:
        display.text(84 + 8 * 18, 32, f"+{game.lives - 8}", COLOR_PLAYER, 20)
    display.text(
        display.width // 2, 8,
        f"LEVEL {game.level_index + 1}/{game.level_count}",
        COLOR_TEXT, 30, Align.CENTER,
    )
    urgent = game.time_left <= 10.0
    display.text(
        display.width - 16, 8, f"TIME {int(math.ceil(game.time_left)):3d}",
        COLOR_DANGER if urgent else COLOR_TEXT, 30, Align.RIGHT,
    )
    display.text(
        display.width - 16, 34, f"GUMS {game.remaining_pacgums}",
        COLOR_TEXT_DIM, 20, Align.RIGHT,
    )
    if game.cheats.any_active:
        display.text(
            display.width // 2, 34, f"CHEATS: {game.cheats.summary()}",
            COLOR_HIGHLIGHT, 20, Align.CENTER,
        )


def draw_game(display: Display, game: Game, elapsed: float) -> None:
    """Draw a full frame of gameplay.

    Args:
        display: Where to draw.
        game: The run being played.
        elapsed: Total running time, used for animations.
    """
    display.clear(COLOR_BACKGROUND)
    view = viewport_for(game.level, display)
    draw_maze(display, game.level, view)
    draw_pacgums(display, game, view, elapsed)
    draw_player(display, game.player, view, elapsed)
    for ghost in game.ghosts:
        draw_ghost(display, ghost, view, game.frightened_timer)
    draw_hud(display, game)
    if game.notice:
        display.text(
            display.width // 2, HUD_HEIGHT + 8, game.notice,
            COLOR_HIGHLIGHT, 34, Align.CENTER,
        )


def _panel(display: Display, height: int) -> int:
    """Dim the screen and return the top of a centred panel.

    Args:
        display: Where to draw.
        height: Panel height in pixels.

    Returns:
        The y coordinate of the panel's top edge.
    """
    top = (display.height - height) // 2
    display.rect(60, top, display.width - 120, height, COLOR_BACKGROUND)
    display.rect(60, top, display.width - 120, 3, COLOR_WALL)
    display.rect(60, top + height - 3, display.width - 120, 3, COLOR_WALL)
    return top


def _menu_list(
    display: Display, items: Sequence[str], selected: int, top: int
) -> None:
    """Draw a vertical list with the current entry highlighted.

    Args:
        display: Where to draw.
        items: The entries to list.
        selected: Index of the highlighted entry.
        top: y coordinate of the first entry.
    """
    for index, label in enumerate(items):
        chosen = index == selected
        y = top + index * 46
        display.text(
            display.width // 2, y, label,
            COLOR_HIGHLIGHT if chosen else COLOR_TEXT, 38, Align.CENTER,
        )
        if chosen:
            marker = display.width // 2 - display.text_width(label, 38) // 2
            display.text(marker - 20, y, ">", COLOR_HIGHLIGHT, 38,
                         Align.RIGHT)


def draw_title(display: Display, subtitle: str) -> None:
    """Draw the game title and a subtitle.

    Args:
        display: Where to draw.
        subtitle: Line shown under the title.
    """
    display.clear(COLOR_BACKGROUND)
    display.text(
        display.width // 2, 70, "PAC-MAN", COLOR_PLAYER, 110, Align.CENTER,
    )
    display.text(
        display.width // 2, 170, subtitle, COLOR_TEXT_DIM, 28, Align.CENTER,
    )


def draw_menu(
    display: Display, selected: int, entries: Sequence[Entry], warning: str
) -> None:
    """Draw the main menu with the top scores beside it.

    Args:
        display: Where to draw.
        selected: Index of the highlighted menu entry.
        entries: The highscore table, best first.
        warning: Optional configuration warning shown at the bottom.
    """
    draw_title(display, "Ghosts! More ghosts!")
    _menu_list(display, MENU_ITEMS, selected, 250)
    display.text(
        display.width // 2, 470, "TOP SCORES", COLOR_TEXT_DIM, 26,
        Align.CENTER,
    )
    if not entries:
        display.text(
            display.width // 2, 500, "no score yet", COLOR_TEXT_DIM, 22,
            Align.CENTER,
        )
    for index, entry in enumerate(entries[:5]):
        display.text(
            display.width // 2 - 120, 500 + index * 26,
            f"{index + 1}. {entry.name}", COLOR_TEXT, 22,
        )
        display.text(
            display.width // 2 + 120, 500 + index * 26, str(entry.score),
            COLOR_TEXT, 22, Align.RIGHT,
        )
    display.text(
        display.width // 2, display.height - 60,
        "arrows or W/S to move, Enter to select, Esc to quit",
        COLOR_TEXT_DIM, 22, Align.CENTER,
    )
    if warning:
        display.text(
            display.width // 2, display.height - 32, warning, COLOR_DANGER,
            20, Align.CENTER,
        )


def draw_highscores(display: Display, entries: Sequence[Entry]) -> None:
    """Draw the full top-ten table.

    Args:
        display: Where to draw.
        entries: The highscore table, best first.
    """
    draw_title(display, "Top 10 highscores")
    if not entries:
        display.text(
            display.width // 2, 300, "Nobody has played yet.",
            COLOR_TEXT_DIM, 30, Align.CENTER,
        )
    for index, entry in enumerate(entries):
        color = COLOR_HIGHLIGHT if index == 0 else COLOR_TEXT
        display.text(
            display.width // 2 - 200, 240 + index * 34,
            f"{index + 1:2d}. {entry.name}", color, 30,
        )
        display.text(
            display.width // 2 + 200, 240 + index * 34, str(entry.score),
            color, 30, Align.RIGHT,
        )
    display.text(
        display.width // 2, display.height - 60, "Esc or Enter to go back",
        COLOR_TEXT_DIM, 24, Align.CENTER,
    )


INSTRUCTION_LINES: Final[tuple[tuple[str, str], ...]] = (
    ("Move", "Arrow keys or W A S D"),
    ("Pause", "P or Esc"),
    ("Goal", "Eat every pacgum to clear the level"),
    ("Super-pacgum", "The four big dots make ghosts edible"),
    ("Ghosts", GHOST_NAMES[0] + " chases, " + GHOST_NAMES[1] + " ambushes, "
     + GHOST_NAMES[2] + " flanks, " + GHOST_NAMES[3] + " is shy"),
    ("Lives", "You lose one on contact and when the timer runs out"),
    ("", ""),
    ("Cheats (for peer review)", ""),
    ("F1", "Toggle invincibility"),
    ("F2", "Skip the current level"),
    ("F3", "Freeze or free the ghosts"),
    ("F4", "Add one life"),
    ("F5", "Toggle extra speed"),
    ("F6", "End the run and go to the score screen"),
)


def draw_instructions(display: Display) -> None:
    """Draw the controls and rules screen.

    Args:
        display: Where to draw.
    """
    draw_title(display, "Controls and rules")
    for index, (label, text) in enumerate(INSTRUCTION_LINES):
        y = 230 + index * 30
        display.text(180, y, label, COLOR_HIGHLIGHT, 26)
        display.text(440, y, text, COLOR_TEXT, 26)
    display.text(
        display.width // 2, display.height - 50, "Esc or Enter to go back",
        COLOR_TEXT_DIM, 24, Align.CENTER,
    )


def draw_pause(display: Display, game: Game, selected: int,
               elapsed: float) -> None:
    """Draw the pause overlay on top of the frozen board.

    Args:
        display: Where to draw.
        game: The run being played.
        selected: Index of the highlighted pause entry.
        elapsed: Total running time, used for animations.
    """
    draw_game(display, game, elapsed)
    top = _panel(display, 260)
    display.text(
        display.width // 2, top + 26, "PAUSED", COLOR_HIGHLIGHT, 60,
        Align.CENTER,
    )
    _menu_list(display, PAUSE_ITEMS, selected, top + 110)
    display.text(
        display.width // 2, top + 216, f"Score so far: {game.score}",
        COLOR_TEXT_DIM, 24, Align.CENTER,
    )


def draw_level_cleared(display: Display, game: Game, elapsed: float) -> None:
    """Draw the short screen shown between two levels.

    Args:
        display: Where to draw.
        game: The run being played.
        elapsed: Total running time, used for animations.
    """
    draw_game(display, game, elapsed)
    top = _panel(display, 180)
    display.text(
        display.width // 2, top + 30,
        f"LEVEL {game.level_index + 1} CLEARED", COLOR_SUCCESS, 52,
        Align.CENTER,
    )
    display.text(
        display.width // 2, top + 100, "Press Enter for the next level",
        COLOR_TEXT, 28, Align.CENTER,
    )


def draw_name_entry(
    display: Display, score: int, name: str, won: bool, cheated: bool
) -> None:
    """Draw the game over or victory screen with the name prompt.

    Args:
        display: Where to draw.
        score: Final score of the run.
        name: What the player has typed so far.
        won: Whether every level was completed.
        cheated: Whether a cheat was used during the run.
    """
    title = "VICTORY!" if won else "GAME OVER"
    draw_title(
        display,
        "Congratulations, you cleared every level!" if won
        else "The ghosts got you.",
    )
    display.text(
        display.width // 2, 220, title,
        COLOR_SUCCESS if won else COLOR_DANGER, 70, Align.CENTER,
    )
    display.text(
        display.width // 2, 310, f"FINAL SCORE {score}", COLOR_TEXT, 44,
        Align.CENTER,
    )
    display.text(
        display.width // 2, 400, "Enter your name (max 10 characters):",
        COLOR_TEXT_DIM, 26, Align.CENTER,
    )
    display.rect(display.width // 2 - 150, 435, 300, 46, COLOR_BACKGROUND)
    display.rect(display.width // 2 - 150, 479, 300, 3, COLOR_WALL)
    display.text(
        display.width // 2, 442, name if name else "_", COLOR_HIGHLIGHT, 40,
        Align.CENTER,
    )
    display.text(
        display.width // 2, 520, "Enter to save, Esc to skip", COLOR_TEXT_DIM,
        24, Align.CENTER,
    )
    if cheated:
        display.text(
            display.width // 2, 560, "Cheats were used during this run.",
            COLOR_TEXT_DIM, 22, Align.CENTER,
        )


def draw_error(display: Display, title: str, detail: str) -> None:
    """Draw a full screen error message.

    Args:
        display: Where to draw.
        title: Short headline.
        detail: Explanation shown under the headline.
    """
    draw_title(display, "Something went wrong")
    display.text(
        display.width // 2, 280, title, COLOR_DANGER, 44, Align.CENTER,
    )
    for index, line in enumerate(_wrap(display, detail, 26, 760)):
        display.text(
            display.width // 2, 350 + index * 30, line, COLOR_TEXT, 26,
            Align.CENTER,
        )
    display.text(
        display.width // 2, display.height - 60,
        "Press Enter to go back to the menu", COLOR_TEXT_DIM, 24, Align.CENTER,
    )


def _wrap(
    display: Display, text: str, size: int, max_width: int
) -> list[str]:
    """Split ``text`` into lines no wider than ``max_width``.

    Args:
        display: Used to measure the text.
        text: The message to wrap.
        size: Font height in pixels.
        max_width: Maximum line width in pixels.

    Returns:
        The wrapped lines.
    """
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and display.text_width(candidate, size) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


DIRECTION_KEYS: Final[dict[str, Direction]] = {
    "up": Direction.UP,
    "w": Direction.UP,
    "down": Direction.DOWN,
    "s": Direction.DOWN,
    "left": Direction.LEFT,
    "a": Direction.LEFT,
    "right": Direction.RIGHT,
    "d": Direction.RIGHT,
}
