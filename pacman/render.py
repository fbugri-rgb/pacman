"""Thin drawing layer over the graphical backend.

Everything the game draws goes through this module, and it exposes only
primitives that have a direct MLX counterpart:

===========================  =====================================
:class:`Display` primitive   MLX equivalent
===========================  =====================================
``Display(...)``             ``mlx_init`` + ``mlx_new_window``
``clear`` / ``rect``         ``mlx_new_image`` + ``mlx_pixel_put``
``disc``                     ``mlx_pixel_put`` over a disc span
``text``                     ``mlx_string_put``
``present``                  ``mlx_put_image_to_window``
``poll``                     ``mlx_key_hook`` + ``mlx_hook``
``tick``                     ``mlx_loop_hook``
``close``                    ``mlx_destroy_window``
===========================  =====================================

No sprite, sound, collision or scene-graph helper of the backend is used,
so the game could be ported to MLX without changing anything but this
file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Final

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from .constants import Color, TARGET_FPS  # noqa: E402

MAX_FRAME_TIME: Final[float] = 0.05


class Align(Enum):
    """Horizontal anchoring of a text string."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass(frozen=True)
class KeyPress:
    """A single key press.

    Attributes:
        name: Backend independent key name, such as ``"up"`` or ``"f1"``.
        char: The character the key produced, empty for non-printable keys.
    """

    name: str
    char: str


class DisplayError(Exception):
    """Raised when no window can be opened."""


class Display:
    """The game window and its offscreen drawing buffer.

    Attributes:
        width: Window width in pixels.
        height: Window height in pixels.
    """

    def __init__(self, width: int, height: int, title: str) -> None:
        """Open a window of the given size.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.

        Raises:
            DisplayError: If the backend cannot open a window, typically
                because no display is available.
        """
        self.width: int = width
        self.height: int = height
        try:
            # Only the video and font subsystems are started: the game
            # has no sound, and initialising the mixer on a machine
            # without an audio device makes shutdown hang for seconds.
            pygame.display.init()
            pygame.font.init()
            pygame.display.set_caption(title)
            self._screen = pygame.display.set_mode((width, height))
        except pygame.error as exc:
            raise DisplayError(f"cannot open a game window: {exc}") from exc
        self._buffer = pygame.Surface((width, height))
        self._clock = pygame.time.Clock()
        self._fonts: dict[int, pygame.font.Font] = {}

    def _font(self, size: int) -> pygame.font.Font:
        """Return a cached font of the requested size.

        Args:
            size: Font height in pixels.

        Returns:
            A font object, built on the backend's built-in typeface so the
            game needs no external asset.
        """
        font = self._fonts.get(size)
        if font is None:
            font = pygame.font.Font(None, size)
            self._fonts[size] = font
        return font

    def tick(self) -> float:
        """Wait for the next frame and return the elapsed time.

        Returns:
            Seconds since the previous call, clamped so that a stalled
            frame cannot teleport actors through walls.
        """
        milliseconds = float(self._clock.tick(TARGET_FPS))
        return min(milliseconds / 1000.0, MAX_FRAME_TIME)

    def poll(self) -> tuple[list[KeyPress], bool]:
        """Collect the key presses queued since the last call.

        Returns:
            The pressed keys and whether the window was closed.
        """
        presses: list[KeyPress] = []
        closed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                closed = True
            elif event.type == pygame.KEYDOWN:
                name = str(pygame.key.name(event.key))
                char = str(getattr(event, "unicode", ""))
                presses.append(KeyPress(name, char))
        return presses, closed

    def clear(self, color: Color) -> None:
        """Fill the whole buffer with a single colour.

        Args:
            color: The fill colour.
        """
        self._buffer.fill(color)

    def rect(
        self, x: int, y: int, width: int, height: int, color: Color
    ) -> None:
        """Draw a filled rectangle.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            width: Rectangle width in pixels.
            height: Rectangle height in pixels.
            color: Fill colour.
        """
        if width <= 0 or height <= 0:
            return
        self._buffer.fill(color, pygame.Rect(x, y, width, height))

    def disc(self, cx: int, cy: int, radius: int, color: Color) -> None:
        """Draw a filled circle.

        Args:
            cx: Centre x in pixels.
            cy: Centre y in pixels.
            radius: Radius in pixels.
            color: Fill colour.
        """
        if radius <= 0:
            return
        pygame.draw.circle(self._buffer, color, (cx, cy), radius)

    def text(
        self,
        x: int,
        y: int,
        message: str,
        color: Color,
        size: int = 24,
        align: Align = Align.LEFT,
    ) -> int:
        """Draw a line of text.

        Args:
            x: Anchor x in pixels, interpreted according to ``align``.
            y: Top edge in pixels.
            message: The text to draw.
            color: Text colour.
            size: Font height in pixels.
            align: Whether ``x`` is the left, centre or right of the text.

        Returns:
            The height of the drawn line in pixels, so callers can stack
            several lines without measuring fonts themselves.
        """
        font = self._font(size)
        surface = font.render(message, True, color)
        width = int(surface.get_width())
        height = int(surface.get_height())
        if align is Align.CENTER:
            x -= width // 2
        elif align is Align.RIGHT:
            x -= width
        self._buffer.blit(surface, (x, y))
        return height

    def text_width(self, message: str, size: int) -> int:
        """Measure a string without drawing it.

        Args:
            message: The text to measure.
            size: Font height in pixels.

        Returns:
            The width the string would occupy, in pixels.
        """
        return int(self._font(size).size(message)[0])

    def present(self) -> None:
        """Push the offscreen buffer to the window."""
        self._screen.blit(self._buffer, (0, 0))
        pygame.display.flip()

    def close(self) -> None:
        """Destroy the window and release the backend."""
        self._fonts.clear()
        pygame.font.quit()
        pygame.display.quit()
