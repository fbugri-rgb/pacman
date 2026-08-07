*This project has been created as part of the 42 curriculum by fbugri.*

# Pac-Man — Ghosts! More ghosts!

A complete Pac-Man written in Python, played on mazes produced by the
imposed **A-Maze-ing** generator. Twelve levels, four ghosts with their
own personalities, super-pacgums, a timer per level, persistent
highscores and a cheat mode for the peer review.

---

## Description

The player eats every pacgum of a maze while four ghosts hunt him. The
mazes are not drawn by hand: each level asks the A-Maze-ing package for a
fresh maze, which is then turned into a playable grid of walls and
corridors. Levels get bigger and the ghosts get faster as the run goes
on; the score and the remaining lives carry over from one level to the
next.

Eating one of the four super-pacgums placed near the corners turns the
tables for a few seconds: the ghosts become edible, flee, and blink just
before they recover. An eaten ghost leaves the board and walks back to
its corner after a delay.

A run ends either when the last life is lost or when the twelfth level is
cleared. Both cases ask for a name and store the score in a top ten that
survives across sessions.

Feature summary:

- Twelve levels, procedurally generated, first one reproducible.
- Four ghosts with distinct hunting behaviours, plus a scatter phase.
- Pacgums, super-pacgums, edible ghosts, lives, per-level time limit.
- Main menu, in-game HUD, pause overlay, game over and victory screens.
- Persistent top-ten highscore table, tolerant to a corrupt file.
- Cheat keys for the peer review.
- Configuration in JSON with comments, every value validated and clamped.
- flake8 clean, `mypy --strict` clean, 108 automated tests.

## Instructions

### Requirements

- Python 3.10 or newer
- pygame
- the A-Maze-ing package, shipped as
  `mazegenerator-2.1.0-py3-none-any.whl` in this repository

### Install

```sh
make install
```

This installs the runtime and development dependencies from
`requirements.txt`, then the A-Maze-ing wheel. The package is installed
as shipped and is never modified.

### Play

```sh
python3 pac-man.py config.json
```

or simply `make run`. Exactly one argument is expected and it must be a
`.json` file; anything else produces a one-line error and a non-zero exit
code.

### Controls

| Key | Action |
| --- | --- |
| Arrow keys, or `W` `A` `S` `D` | Move |
| `P` or `Esc` | Pause and resume |
| Up / Down, `Enter` | Navigate and validate in the menus |
| `Esc` | Leave a menu screen, quit from the main menu |

### Cheat keys (peer review)

Available while playing, and switched off by setting `cheats_enabled` to
`false` in the configuration. Using one marks the run, which is shown on
the score screen.

| Key | Cheat |
| --- | --- |
| `F1` | Toggle invincibility |
| `F2` | Skip the current level |
| `F3` | Freeze or free the ghosts |
| `F4` | Add one life |
| `F5` | Toggle extra speed |
| `F6` | End the run and go to the score screen |

### Other make rules

| Rule | Effect |
| --- | --- |
| `make install` | Install the dependencies and the maze generator |
| `make run` | Launch the game on `config.json` |
| `make debug` | Launch it under `pdb` |
| `make lint` | `flake8 .` and `mypy` with the required flags |
| `make lint-strict` | `flake8 .` and `mypy . --strict` |
| `make test` | Run the test suite |
| `make package` | Build the distributable archive |
| `make clean` / `make fclean` | Remove caches / also remove the build output |

## Configuration

The game reads a JSON file **extended with comments**: `#` and `//` run
to the end of the line, `/* ... */` spans several lines. Comments are
stripped before parsing, and markers inside strings are left alone, so a
filename such as `"a#b.json"` survives untouched. Line numbers are
preserved, so a syntax error is reported at the line actually written.

Every key is optional. A missing, misspelled, mistyped or out-of-range
value is replaced by a safe default, the correction is printed on stderr
at startup, and the game starts anyway. Unknown keys are ignored. An
empty object `{}` is a perfectly valid configuration.

| Key | Type | Range | Default | Meaning |
| --- | --- | --- | --- | --- |
| `highscore_filename` | string | — | `highscores.json` | Where the top ten is stored |
| `lives` | int | 1 – 99 | 3 | Lives at the start of a run |
| `points_per_pacgum` | int | 0 – 100000 | 10 | Score for one pacgum |
| `points_per_super_pacgum` | int | 0 – 100000 | 50 | Score for one super-pacgum |
| `points_per_ghost` | int | 0 – 100000 | 200 | Score for one eaten ghost |
| `seed` | int | 1 – 2147483647 | 42 | Seed of the **first** level only |
| `pacgum` | int | 1 – 100000 | 42 | Pacgums per level, clamped to the corridors available |
| `level_max_time` | number | 10 – 3600 | 90 | Time limit of a level, in seconds |
| `player_speed` | number | 1.0 – 20.0 | 6.0 | Tiles per second |
| `super_pacgum_duration` | number | 0.5 – 120.0 | 8.0 | How long ghosts stay edible |
| `ghost_respawn_delay` | number | 0.5 – 120.0 | 6.0 | How long an eaten ghost stays away |
| `cheats_enabled` | bool | — | `true` | Enables the `F1`–`F6` keys |
| `level` | array | at least 10 after padding | ten default levels | The levels, played in order |

Each entry of `level` accepts:

| Key | Type | Range | Meaning |
| --- | --- | --- | --- |
| `width` | int | 7 – 35 | Maze width in generator cells |
| `height` | int | 7 – 35 | Maze height in generator cells |
| `pacgum` | int | 1 – 100000 | Overrides the global value |
| `max_time` | number | 10 – 3600 | Overrides the global time limit |
| `ghost_speed` | number | 1.0 – 20.0 | Ghost speed for that level, default 4.5 |

Two details are worth knowing. A maze of `width` cells becomes a grid of
`2 × width + 1` tiles, because the walls occupy real tiles. And the
shipped file sets `pacgum` to a deliberately large number so that every
corridor is filled: since pacgums are spread over the whole maze,
clearing a level means visiting nearly all of it anyway, and filling the
corridors at least lets the player see what is left.

Fewer than ten levels are padded up to ten, as required. More than ten
are all kept.

## Highscore

Scores are stored as a JSON array of `{"name": ..., "score": ...}`
objects, at the path given by `highscore_filename`.

- The table is loaded when the game starts and saved when a run ends.
- A name is asked on both endings, game over and victory.
- Names keep letters, digits and spaces only, and are cut to ten
  characters; an empty result falls back to `PLAYER`.
- Scores must be non-negative integers; anything else is rejected.
- Only the ten best are kept, sorted by decreasing score.
- The table is shown from the main menu, and after a run.

Robustness was treated as a feature, not as an afterthought:

- A missing file is normal, not an error: the table starts empty.
- A corrupt file, a wrong shape, or malformed entries produce an empty or
  partial table plus a warning shown in the interface. Nothing raises.
- Saving goes through a temporary file and an atomic rename, so an
  interrupted write can never truncate an existing table.
- A save that fails, for instance on a read-only location, is reported
  and the game keeps running.

## Maze generation

The mazes come from the imposed A-Maze-ing package, used **exactly as
shipped**. Nothing is patched, vendored or subclassed; the whole
adaptation lives in `pacman/maze.py`, which is the only file aware that
the package exists.

### Adapting to their interface

The generator is instantiated through a small probe: several plausible
constructor signatures are tried in order and the first accepted one is
kept. This is not defensive decoration — the package documentation and
the package code disagree on the keyword names, and the wheel is
reinstalled by the reviewer. `perfect` is set to `False`, as required.

The generator seeds Python's **global** random source when it runs. The
game therefore never uses the module-level `random` functions: it owns
private `random.Random` instances, so that maze generation cannot
correlate with ghost behaviour or collectible placement.

### From cells to tiles

The package returns a grid of cells, each holding four wall bits (north,
east, south and west). A cell grid of `w × h` becomes a tile grid of
`(2w + 1) × (2h + 1)`: odd coordinates are cell centres, even ones are
the walls between them.

A passage between two neighbouring cells is opened only when **both**
cells agree that there is no wall between them. Trusting a single side
would let a stray bit punch holes through the maze. The outer border is
always solid.

### Filling a level

1. The tile grid is built from the generator output.
2. A flood fill computes the largest connected corridor area. This
   matters because `perfect = False` allows isolated pockets, and a
   pacgum in a pocket would make a level impossible to finish.
3. The player spawns at the corridor closest to the centre of that area.
4. Four ghost spawns are chosen, one per corner, always reachable.
5. Four super-pacgums are placed near the four corners.
6. Pacgums fill the remaining corridors, up to the configured count.

Everything after step 2 happens inside the reachable area, so every level
is guaranteed to be winnable. A test asserts that property over four
maze sizes and three seeds.

If the package is missing, or raises, or returns something unusable, the
failure becomes a `MazeError` and the game shows an error screen. It
never crashes and never prints a traceback.

## Implementation

### Movement

Actors do not move in pixels. Each one remembers the tile it is leaving,
the tile it is entering, and how far along it is between the two. The
drawing interpolates between the two tiles, so movement looks smooth,
but every decision — turning, eating, colliding — happens exactly on a
tile boundary.

This removes a whole family of bugs by construction: an actor can never
end up half inside a wall, and a collision cannot slip between two
frames. A requested turn that is not possible yet is buffered and applied
at the next junction, and a half-turn is applied immediately, which is
what makes the controls feel right.

All speeds are expressed in tiles per second and multiplied by the real
frame delta, which is clamped: a machine that stalls for a second cannot
teleport a ghost through a wall.

### Ghosts

The four ghosts each compute their own target tile:

| Ghost | Behaviour |
| --- | --- |
| Blinky | Heads straight for the player |
| Pinky | Aims four tiles ahead of the player, to cut him off |
| Inky | Targets the player's tile mirrored through Blinky's, so he flanks |
| Clyde | Chases, but retreats to his corner when he gets within eight tiles |

They alternate between chasing and a scatter phase where they retreat
towards their corners, and they never turn back on themselves at a
junction unless there is no other way out. A frightened ghost inverts the
rule and maximises its distance from the player. Ties between equally
good directions are broken randomly, so two ghosts in the same corridor
do not walk in lockstep.

### Error handling

No traceback ever reaches the terminal. There are three domain
exceptions, `ConfigError`, `MazeError` and `DisplayError`, raised at the
three boundaries where the outside world can misbehave, and the entry
script converts them into a one-line message and an exit code. Files are
handled with context managers, and the display is closed in a `finally`
block, so a window is never left open.

| Situation | Result |
| --- | --- |
| Wrong number of arguments, or not a `.json` | Message, usage line, exit 1 |
| Unreadable or invalid configuration | Message with the line number, exit 1 |
| Out-of-range configuration values | Clamped, reported, game runs |
| Maze generator missing or failing | Error screen inside the game |
| Display unavailable | Message, exit 1 |
| `Ctrl+C` | Message, exit 130 |

### Quality

```sh
make lint          # flake8 . and mypy with the required flags
make lint-strict   # flake8 . and mypy . --strict
make test          # 108 tests
```

All three are clean. Every function carries type hints and a PEP 257
docstring. The tests cover the comment stripper, the configuration
clamping, the highscore validation, the maze conversion and the game
rules, and include property tests: nothing unreachable in a maze, nobody
ever inside a wall, and a score that never decreases over two simulated
minutes of random play.

## General software architecture

Eight modules, about 3300 lines, each with one responsibility and
depending only on the ones below it.

```
                        pac-man.py
                     (CLI, exit codes)
                            |
                       pacman/app.py
                 (state machine, input, run loop)
                       /          \
                pacman/ui.py    pacman/game.py
              (screen drawing)   (rules, levels, score)
                     |               |
             pacman/render.py   pacman/entities.py
             (backend facade)   (player, ghosts, AI)
                     |               |
                  pygame        pacman/maze.py
                                (A-Maze-ing adapter)
                                      |
                                 mazegenerator

     pacman/config.py       pacman/highscores.py    pacman/constants.py
     (JSONC, validation)    (persistence)           (enums, colours)
```

| Module | Responsibility |
| --- | --- |
| `pac-man.py` | Argument checking, loading, exit codes |
| `pacman/app.py` | Screen state machine, key dispatch, frame loop |
| `pacman/ui.py` | Draws every screen and the board |
| `pacman/render.py` | The only file importing the graphics backend |
| `pacman/game.py` | Rules: scoring, lives, timer, level progression, cheats |
| `pacman/entities.py` | Movement and ghost intelligence |
| `pacman/maze.py` | Adapts the imposed generator, builds levels |
| `pacman/config.py` | Comment stripping, validation, clamping |
| `pacman/highscores.py` | Sanitising, loading and atomic saving |
| `pacman/constants.py` | Enums, colours, sizes shared by everyone |

Two properties of this layout are deliberate.

**The backend is replaceable.** `pacman/render.py` is the only module
that imports pygame, and it exposes nothing but primitives that MLX also
provides: a window, filled rectangles and discs, text, key events and a
frame tick. The correspondence table is in the module docstring. Porting
the game to MLX means rewriting that one file.

**The rules do not know about the screen.** `game.py` and `entities.py`
have no notion of pixels, windows or key codes; they work in tiles and
seconds. That is what makes them testable without a display, and the
whole test suite runs headless.

## Resources

- The 42 subject, *Pac-Man — Ghosts! More ghosts!*
- The imposed A-Maze-ing package, used as shipped
- [pygame documentation](https://www.pygame.org/docs/)
- [The Pac-Man Dossier](https://pacman.holenet.info/) by Jamey Pittman,
  for the original ghost targeting rules and the scatter/chase cycle
- Python documentation for `json`, `dataclasses`, `enum` and `tempfile`

### Use of AI

Claude (Anthropic) was used as a pair-programming assistant during the
whole project. Concretely:

- **Design discussion.** Arguing the module split, and in particular the
  decision to confine the graphics backend behind one facade so that an
  MLX port stays possible.
- **Code drafting.** First versions of the configuration loader, the
  screen-drawing functions and the test suite, all reviewed, corrected
  and adjusted by hand afterwards.
- **The maze adapter.** Written together, then verified against the real
  package output rendered as ASCII, which is how the constructor
  signature mismatch and the global-seeding behaviour were found.
- **Debugging.** Narrowing down the several-second freeze at exit to the
  audio subsystem being started by the blanket pygame initialisation.
- **Reviewing.** Passing over the code for missing type hints, missing
  docstrings and unhandled exception paths before each lint run.
- **Documentation.** Drafting this README and the project management
  documents from the notes taken during development.

Everything committed was read, understood and, where needed, rewritten.
The parts that took the most human decisions are the maze adaptation, the
level balance, and the movement model.

## Project management

The planning, the progress against it, the technical decisions, the risk
register, the acceptance test plan and the blocking points met are in the
[project-management/](project-management/) directory:

| Document | Content |
| --- | --- |
| [01-timeline.md](project-management/01-timeline.md) | Milestones, Gantt chart, Kanban board |
| [02-progress.md](project-management/02-progress.md) | Progress measured against the plan |
| [03-analysis-and-choices.md](project-management/03-analysis-and-choices.md) | Requirement analysis and technical decisions |
| [04-risks.md](project-management/04-risks.md) | Risk register with mitigations |
| [05-organisation.md](project-management/05-organisation.md) | Organisation, roles, working rules |
| [06-acceptance-tests.md](project-management/06-acceptance-tests.md) | Acceptance test plan |
| [07-blocking-points.md](project-management/07-blocking-points.md) | Blocking points and how they were solved |

## Packaging

The game is distributed on Itch.io, at
`https://fbugri.itch.io/pacman` — *replace this line with the real page
once the build is uploaded.* It can also be built locally:

```sh
./build.sh
```

The script checks the toolchain, freezes the game with PyInstaller
through `pacman.spec`, copies the configuration next to the produced
binary and zips the result under `dist/`. The packaged game starts with
no argument; it uses the `config.json` sitting next to the executable if
there is one, and the embedded copy otherwise. Both the spec and the
script live at the root of the repository and can be re-run from a clean
tree during the review.
