"""Application state machine and main loop.

The loop is deliberately dull: read the keys, advance the simulation by
the measured frame time, draw.  All the branching lives in the per-screen
key handlers below.
"""

from __future__ import annotations

from typing import Callable, Final

from . import ui
from .config import GameConfig
from .constants import (
    Screen,
    TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .game import Game, GameStatus
from .highscores import HighscoreTable, MAX_NAME_LENGTH
from .maze import MazeError
from .render import Display, KeyPress

CONFIRM_KEYS: Final[frozenset[str]] = frozenset({"return", "enter", "space"})
BACK_KEYS: Final[frozenset[str]] = frozenset({"escape"})
UP_KEYS: Final[frozenset[str]] = frozenset({"up", "w"})
DOWN_KEYS: Final[frozenset[str]] = frozenset({"down", "s"})


class App:
    """Owns the window, the current screen and the running game.

    Attributes:
        config: The validated configuration.
        screen: The screen currently displayed.
        game: The run in progress, or ``None`` outside of a game.
    """

    def __init__(self, config: GameConfig, display: Display) -> None:
        """Wire the application together.

        The highscore table is loaded here, at game start, as required.

        Args:
            config: A validated configuration.
            display: An already opened window.
        """
        self.config: GameConfig = config
        self.screen: Screen = Screen.MENU
        self.game: Game | None = None
        self._display = display
        self._table = HighscoreTable(config.highscore_filename)
        self._table.load()
        self._menu_index = 0
        self._pause_index = 0
        self._name = ""
        self._won = False
        self._error = ""
        self._elapsed = 0.0
        self._handlers: dict[Screen, Callable[[KeyPress], None]] = {
            Screen.MENU: self._on_menu_key,
            Screen.HIGHSCORES: self._on_back_only_key,
            Screen.INSTRUCTIONS: self._on_back_only_key,
            Screen.ERROR: self._on_back_only_key,
            Screen.PLAYING: self._on_playing_key,
            Screen.PAUSED: self._on_paused_key,
            Screen.LEVEL_CLEARED: self._on_level_cleared_key,
            Screen.NAME_ENTRY: self._on_name_entry_key,
        }

    @property
    def warnings(self) -> list[str]:
        """Return every warning worth showing the player, most urgent first.

        Highscore problems come first, newest first, because unlike the
        config warnings they are not printed on stderr: a failed save
        would otherwise stay hidden behind a startup warning.
        """
        return self._table.warnings[::-1] + list(self.config.warnings)

    def run(self) -> None:
        """Run the game until the player quits or closes the window."""
        while self.screen is not Screen.QUIT:
            delta = self._display.tick()
            self._elapsed += delta
            presses, closed = self._display.poll()
            if closed:
                break
            for press in presses:
                handler = self._handlers.get(self.screen)
                if handler is not None:
                    handler(press)
            self._update(delta)
            self._draw()

    def _update(self, delta: float) -> None:
        """Advance the running game and react to its outcome.

        Args:
            delta: Elapsed time in seconds.
        """
        if self.screen is not Screen.PLAYING or self.game is None:
            return
        self.game.update(delta)
        status = self.game.status
        if status is GameStatus.LEVEL_CLEARED:
            self.screen = Screen.LEVEL_CLEARED
        elif status is GameStatus.GAME_OVER:
            self._finish(won=False)
        elif status is GameStatus.VICTORY:
            self._finish(won=True)

    def _draw(self) -> None:
        """Draw the current screen."""
        if self.screen is Screen.MENU:
            ui.draw_menu(
                self._display, self._menu_index, self._table.entries,
                self.warnings[0] if self.warnings else "",
            )
        elif self.screen is Screen.HIGHSCORES:
            ui.draw_highscores(self._display, self._table.entries)
        elif self.screen is Screen.INSTRUCTIONS:
            ui.draw_instructions(self._display)
        elif self.screen is Screen.ERROR:
            ui.draw_error(self._display, "Cannot start the game", self._error)
        elif self.screen is Screen.NAME_ENTRY:
            ui.draw_name_entry(
                self._display, self._final_score, self._name, self._won,
                self._cheated,
            )
        elif self.game is not None:
            self._draw_board(self.game)
        self._display.present()

    def _draw_board(self, game: Game) -> None:
        """Draw the maze, possibly under an overlay.

        Args:
            game: The run to draw.
        """
        if self.screen is Screen.PAUSED:
            ui.draw_pause(
                self._display, game, self._pause_index, self._elapsed
            )
        elif self.screen is Screen.LEVEL_CLEARED:
            ui.draw_level_cleared(self._display, game, self._elapsed)
        else:
            ui.draw_game(self._display, game, self._elapsed)

    @property
    def _final_score(self) -> int:
        """Return the score of the run that just ended."""
        return self.game.score if self.game is not None else 0

    @property
    def _cheated(self) -> bool:
        """Tell whether a cheat was used during the run that just ended."""
        return self.game is not None and self.game.cheats.used

    def _start_game(self) -> None:
        """Begin a new run, reporting maze failures on the error screen."""
        try:
            self.game = Game(self.config)
        except MazeError as exc:
            self.game = None
            self._error = str(exc)
            self.screen = Screen.ERROR
            return
        self.screen = Screen.PLAYING

    def _finish(self, won: bool) -> None:
        """Move to the name prompt once a run is over.

        Args:
            won: Whether every level was completed.
        """
        self._won = won
        self._name = ""
        self.screen = Screen.NAME_ENTRY

    def _save_score(self) -> None:
        """Store the final score and write the table back to disk."""
        if self.game is not None:
            self._table.add(self._name, self.game.score)
            self._table.save()

    def _to_menu(self) -> None:
        """Drop the current run and go back to the main menu."""
        self.game = None
        self.screen = Screen.MENU

    def _on_menu_key(self, press: KeyPress) -> None:
        """Handle a key press on the main menu.

        Args:
            press: The key that was pressed.
        """
        if press.name in UP_KEYS:
            self._menu_index = (self._menu_index - 1) % len(ui.MENU_ITEMS)
        elif press.name in DOWN_KEYS:
            self._menu_index = (self._menu_index + 1) % len(ui.MENU_ITEMS)
        elif press.name in BACK_KEYS:
            self.screen = Screen.QUIT
        elif press.name in CONFIRM_KEYS:
            self._activate_menu_item()

    def _activate_menu_item(self) -> None:
        """Run the action of the highlighted main menu entry."""
        if self._menu_index == 0:
            self._start_game()
        elif self._menu_index == 1:
            self.screen = Screen.HIGHSCORES
        elif self._menu_index == 2:
            self.screen = Screen.INSTRUCTIONS
        else:
            self.screen = Screen.QUIT

    def _on_back_only_key(self, press: KeyPress) -> None:
        """Return to the menu from a read-only screen.

        Args:
            press: The key that was pressed.
        """
        if press.name in BACK_KEYS or press.name in CONFIRM_KEYS:
            self.screen = Screen.MENU

    def _on_playing_key(self, press: KeyPress) -> None:
        """Handle a key press during gameplay.

        Args:
            press: The key that was pressed.
        """
        if self.game is None:
            return
        direction = ui.DIRECTION_KEYS.get(press.name)
        if direction is not None:
            self.game.steer(direction)
            return
        if press.name in BACK_KEYS or press.name == "p":
            self._pause_index = 0
            self.screen = Screen.PAUSED
            return
        if self.config.cheats_enabled:
            self._apply_cheat(press.name)

    def _apply_cheat(self, key: str) -> None:
        """Trigger the cheat bound to ``key``, if any.

        Args:
            key: Name of the pressed key.
        """
        if self.game is None:
            return
        actions: dict[str, Callable[[], None]] = {
            "f1": self.game.toggle_invincible,
            "f2": self.game.skip_level,
            "f3": self.game.toggle_frozen,
            "f4": self.game.grant_life,
            "f5": self.game.toggle_fast,
            "f6": self.game.end_run,
        }
        action = actions.get(key)
        if action is not None:
            action()

    def _on_paused_key(self, press: KeyPress) -> None:
        """Handle a key press on the pause overlay.

        Args:
            press: The key that was pressed.
        """
        if press.name in UP_KEYS or press.name in DOWN_KEYS:
            self._pause_index = 1 - self._pause_index
        elif press.name in BACK_KEYS or press.name == "p":
            self.screen = Screen.PLAYING
        elif press.name in CONFIRM_KEYS:
            if self._pause_index == 0:
                self.screen = Screen.PLAYING
            else:
                self._to_menu()

    def _on_level_cleared_key(self, press: KeyPress) -> None:
        """Handle a key press on the level cleared screen.

        Args:
            press: The key that was pressed.
        """
        if self.game is None or press.name not in CONFIRM_KEYS:
            return
        try:
            advanced = self.game.next_level()
        except MazeError as exc:
            self._error = str(exc)
            self.screen = Screen.ERROR
            return
        if advanced:
            self.screen = Screen.PLAYING
        else:
            self._finish(won=True)

    def _on_name_entry_key(self, press: KeyPress) -> None:
        """Handle a key press on the name prompt.

        Args:
            press: The key that was pressed.
        """
        if press.name in BACK_KEYS:
            self._to_menu()
            return
        if press.name == "backspace":
            self._name = self._name[:-1]
            return
        if press.name in {"return", "enter"}:
            self._save_score()
            self._to_menu()
            return
        char = press.char
        if len(self._name) < MAX_NAME_LENGTH and (
            char.isalnum() or char == " "
        ):
            self._name += char


def run_game(config: GameConfig) -> None:
    """Open a window and play until the player quits.

    Args:
        config: A validated configuration.

    Raises:
        DisplayError: If no window can be opened.
    """
    display = Display(WINDOW_WIDTH, WINDOW_HEIGHT, TITLE)
    try:
        App(config, display).run()
    finally:
        display.close()
