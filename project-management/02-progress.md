# Progress tracking

Progress is tracked against the milestones of
[01-timeline.md](01-timeline.md). The rule used throughout: a work
package is either *done* or *not started*; there is no percentage, since
a self-reported "80% done" carries no information.

## Milestones

| Milestone | Target | Reached | Comment |
| --- | --- | --- | --- |
| M1 Skeleton runs | 2026-07-22 | 2026-07-22 | On time |
| M2 Maze on screen | 2026-07-27 | 2026-07-28 | One day late, see B1 in [07-blocking-points.md](07-blocking-points.md) |
| M3 Game loop playable | 2026-08-01 | 2026-08-01 | Recovered the day lost on M2 by dropping the ghost tunnel idea |
| M4 Feature complete | 2026-08-04 | 2026-08-04 | On time |
| M5 Defense ready | 2026-08-07 | 2026-08-07 | On time |

## Work packages

| # | Work package | State | Evidence |
| --- | --- | --- | --- |
| 1 | Subject analysis, setup | done | `Makefile`, `setup.cfg`, `.gitignore` |
| 2 | Config loader | done | `pacman/config.py`, 22 tests |
| 3 | Maze adapter | done | `pacman/maze.py`, 36 tests |
| 4 | Entities and movement | done | `pacman/entities.py`, 36 tests with the rules |
| 5 | Game rules and levels | done | `pacman/game.py`, 12 levels in `config.json` |
| 6 | Rendering and UI | done | `pacman/render.py`, `pacman/ui.py`, `pacman/app.py` |
| 7 | Highscores and menus | done | `pacman/highscores.py`, 14 tests |
| 8 | Tests and linters | done | 109 tests, `make lint` and `make lint-strict` clean |
| 9 | Packaging and docs | done | `pacman.spec`, `build.sh`, `README.md`, this directory |

## Quality indicators at M5

| Indicator | Target | Measured |
| --- | --- | --- |
| `flake8 .` | no finding | no finding |
| `mypy` with the subject flags | no error | no error |
| `mypy . --strict` | no error (bonus) | no error |
| Test suite | all green | 109 passed |
| Uncaught traceback in a session | zero | zero |
| Levels shipped | at least 10 | 12 |

## What the numbers do not say

The test count is a weak indicator on its own: the parts that took the
longest to get right are the maze adapter and the movement code, and
those are covered by *property* tests (nothing unreachable, never inside
a wall, score never decreasing) rather than by many small ones. Those
few tests are worth more than the rest of the suite put together.
