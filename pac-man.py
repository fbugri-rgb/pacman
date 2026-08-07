#!/usr/bin/env python3
"""Command line entry point.

Usage:
    python3 pac-man.py config.json

Every foreseeable failure is turned into a one-line message on stderr and
a non-zero exit code; a traceback should never reach the terminal.
"""

from __future__ import annotations

import os
import sys

from pacman.app import run_game
from pacman.config import ConfigError, GameConfig, load_config
from pacman.render import DisplayError

USAGE = "usage: python3 pac-man.py <config.json>"


def bundled_config() -> str | None:
    """Return the configuration shipped inside a packaged build.

    A file sitting next to the executable wins over the embedded copy, so
    that a player can retune the levels without rebuilding anything.

    Returns:
        The path to the configuration to use, or ``None`` when the game
        runs from the sources, where an argument is always required.
    """
    root: object = getattr(sys, "_MEIPASS", None)
    if not isinstance(root, str):
        return None
    beside = os.path.join(os.path.dirname(sys.executable), "config.json")
    if os.path.isfile(beside):
        return beside
    return os.path.join(root, "config.json")


def report_warnings(config: GameConfig) -> None:
    """Print the corrections the loader had to make.

    Args:
        config: The configuration that was just loaded.
    """
    if not config.warnings:
        return
    print(
        f"config: {len(config.warnings)} value(s) were adjusted:",
        file=sys.stderr,
    )
    for warning in config.warnings:
        print(f"  - {warning}", file=sys.stderr)


def main(argv: list[str]) -> int:
    """Load the configuration and start the game.

    Args:
        argv: Command line arguments, without the program name.

    Returns:
        The process exit code.
    """
    if not argv:
        fallback = bundled_config()
        if fallback is not None:
            argv = [fallback]
    if len(argv) != 1:
        print(
            f"error: exactly one argument is expected, got {len(argv)}",
            file=sys.stderr,
        )
        print(USAGE, file=sys.stderr)
        return 1
    try:
        config = load_config(argv[0])
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    report_warnings(config)
    try:
        run_game(config)
    except DisplayError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
