# Timeline

The project was split into nine work packages over three weeks, from
**2026-07-20** to **2026-08-07**. Each package ends on a demonstrable
result rather than on an amount of code written, so that a slip is
visible the day it happens instead of at the end.

## Milestones

| # | Milestone | Target | Definition of done |
| --- | --- | --- | --- |
| M1 | Skeleton runs | 2026-07-22 | `make run` opens a window and closes cleanly |
| M2 | Maze on screen | 2026-07-27 | A-Maze-ing output drawn as a playable tile grid |
| M3 | Game loop playable | 2026-08-01 | Player, ghosts, pacgums, lives and score all work |
| M4 | Feature complete | 2026-08-04 | Menus, highscores, cheats, ten levels |
| M5 | Defense ready | 2026-08-07 | Lint clean, tests green, packaged build, docs written |

## Gantt chart

Each column is one day; `#` is planned work, `=` is slack kept on purpose.

```
Work package                    Jul20  Jul23  Jul26  Jul29  Aug01  Aug04  Aug07
                                  |      |      |      |      |      |      |
1  Subject analysis, setup       ###
2  Config loader (JSONC)         ####
3  Maze adapter                    ######
4  Entities and movement               #####
5  Game rules and levels                  #####
6  Rendering and UI screens                  ######
7  Highscores and menus                          ####
8  Tests, flake8, mypy                    ##       #####
9  Packaging and documentation                          #####
   Slack / defense rehearsal                                  ====
```

Work package 8 is deliberately split: the linters were wired in from the
third day and run on every change, and only the test suite itself was
written at the end. Chasing typing errors in one big batch at the end of
a project is the classic way to lose a day.

## Kanban board (state at 2026-10-14)

```
BACKLOG            | IN PROGRESS | REVIEW              | DONE
-------------------+-------------+---------------------+----------------------
Sound effects      |  --         |  --                 | Config loader
Ghost tunnel       |             |                     | Maze adapter
Sprite artwork     |             |                     | Entities and AI
Level editor       |             |                     | Game rules, levels
                   |             |                     | Rendering and UI
                   |             |                     | Highscores
                   |             |                     | Cheat mode
                   |             |                     | Tests and linters
                   |             |                     | Packaging script
                   |             |                     | Documentation
                   |             |                     | Itch.io upload
                   |             |                     | CI release builds
                   |             |                     |  (Linux, Windows,
                   |             |                     |   macOS)
```

The Itch.io upload, still waiting for its store page at M5, was
finished on 2026-10-14. Since PyInstaller cannot cross-compile, it came
with a GitHub Actions workflow that freezes the game on one runner per
platform and pushes the three builds with butler.

The backlog column holds ideas that are explicitly *out of scope*: they
are written down so that they stop competing for attention with the
mandatory requirements.
