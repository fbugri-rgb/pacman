# Pac-Man — Ghosts! More ghosts!: how the code works

This document explains the project the way you would present it to someone:
first the one-minute version, then one frame of the game followed through the
code, then each file in detail, and finally the questions people usually ask.

---

## Part 1: The high-level summary

### The one-sentence version

> A complete Pac-Man in Python and pygame, where every level's maze comes from
> the imposed A-Maze-ing generator. Four ghosts with their own personalities,
> twelve levels, persistent highscores, and a configuration file that can never
> crash the game.

### What the subject asked for, and what was built

| Requirement | How it is met |
|---|---|
| Use the imposed maze generator, unmodified | `maze.py` is the only file that touches it, through an adapter |
| At least 10 levels | 12 in `config.json`; fewer are padded up to 10 |
| Pacgums, super-pacgums, ghosts, lives, timer | `game.py` and `entities.py` |
| JSON config with comments, robust to bad values | `config.py`: comments stripped, every value clamped |
| Persistent top-ten highscores | `highscores.py`: atomic save, tolerant to corrupt files |
| Menu, HUD, pause, game over, victory | `app.py` (state machine) + `ui.py` (drawing) |
| Cheat mode for the review | `F1`–`F6`, in `game.py` |
| flake8 + mypy, no tracebacks | `mypy --strict` clean, 3 domain exceptions caught at the edges |

### The architecture in one picture

Each layer only depends on the layers below it:

```
                 pac-man.py          ← command line, exit codes
                     │
                  app.py             ← screens (state machine) + main loop
                 ╱       ╲
             ui.py       game.py     ← drawing        │  rules
               │            │
           render.py   entities.py   ← pygame facade  │  player + ghost AI
               │            │
            pygame       maze.py     ← adapter around the imposed generator
                            │
                      mazegenerator

  side modules used by everyone: config.py · highscores.py · constants.py
```

### The three ideas that make it work

If you only have time to explain three things, explain these:

1. **The rules never know about the screen.** `game.py` and `entities.py`
   work in *tiles* and *seconds*, never pixels or key codes. This is what lets
   the whole game be tested without opening a window.
2. **Movement happens tile by tile.** An actor is always "leaving tile A,
   entering tile B, X% of the way". It is drawn smoothly in between, but every
   decision (turn, eat, collide) happens exactly on a tile. Nobody can end up
   half inside a wall.
3. **The outside world is untrusted.** The config file, the highscore file,
   the maze generator and the display can each fail. Each one sits behind its
   own boundary that turns failures into a clean message: `ConfigError`,
   warnings for highscores, `MazeError` and `DisplayError`.

---

## Part 2: Following the game through the code

The easiest way to explain the code is to follow what happens from launch to
one frame of gameplay.

### Step 1: Launch (`pac-man.py`)

```sh
python3 pac-man.py config.json
```

- `main()` checks there is **exactly one** argument. If not, it prints the
  usage and exits with code 1.
- `load_config()` reads the file, strips the comments and validates every
  value. Out-of-range values are clamped and printed as warnings on stderr,
  and the game still starts.
- `run_game()` opens the window and runs the app. The window is closed in a
  `finally` block, so it is never left open.

### Step 2: The main menu (`app.py`)

`App.__init__` loads the highscore table and sets `screen = Screen.MENU`.
The `run()` loop does only three things, about 60 times per second:

```python
delta = display.tick()        # 1. measure the time since the last frame
presses = display.poll()      #    and read the keys
handler(press)                # 2. send each key to the current screen's handler
self._update(delta)           # 3. advance the game, then
self._draw()                  #    draw the current screen
```

Choosing *Start Game* calls `_start_game()`, which creates `Game(config)`.

### Step 3: Building a level (`game.py` → `maze.py`)

`Game._generate(0)` calls `build_level(width, height, pacgum, seed)`:

1. **Generate:** call the imposed `MazeGenerator` with `perfect=False`, so the
   maze has loops.
2. **Convert:** a grid of *cells with wall bits* becomes a grid of *tiles*
   where walls are real squares. A 15×15 maze becomes 31×31 tiles.
3. **Keep only the reachable part:** a flood fill finds the largest connected
   corridor area.
4. **Place things:** the player near the centre, the 4 ghosts in the 4
   corners, the 4 super-pacgums near the corners, and pacgums everywhere else.

Level 1 always uses the configured seed (`42`), so it is always the same maze.
Later levels use random seeds.

### Step 4: One frame of gameplay (`Game.update`)

The player presses ←. `App._on_playing_key` maps the key to
`Direction.LEFT` and calls `game.steer()`. Then `Game.update(delta)` runs:

```
tick timers  →  move player  →  collect pacgum  →  move ghosts  →  check contacts  →  level done?
```

1. **Timers:** the level clock counts down (at 0: *TIME UP!*, the player loses
   a life and the level restarts). The super-pacgum timer counts down. The
   ghosts alternate between *scatter* (7 s) and *chase* (20 s).
2. **Player moves:** `Actor.update` advances `progress`. At each new tile it
   asks the "picker" which way to go next.
3. **Collect:** a pacgum on the player's tile gives +10. A super-pacgum gives
   +50 and frightens every ghost.
4. **Ghosts move:** each one computes its target tile and picks the direction
   that gets closest to it.
5. **Contacts:** touching an edible ghost gives +200 and sends it home.
   Touching a normal ghost costs a life (unless invincible).
6. **Level done:** if no pacgum is left, the status becomes `LEVEL_CLEARED`.

### Step 5: Drawing (`ui.py` → `render.py`)

`ui.draw_game()` reads the game state (never modifies it) and calls
`Display.rect`, `Display.disc` and `Display.text`. `render.py` is the only file
that calls pygame.

### Step 6: End of the run

When the last life is lost (`GAME_OVER`) or level 12 is cleared (`VICTORY`),
`App._finish()` shows the name prompt. Enter saves the score to the top ten.

---

## Part 3: The files in detail

### Map of the repository

```
pacman/
├── pac-man.py              entry point: arguments, exit codes
├── config.json             the 12 levels and every setting, with comments
├── pacman/
│   ├── constants.py        enums (Direction, Screen, GhostState), colours, sizes
│   ├── config.py           JSON-with-comments loader + validation
│   ├── maze.py             adapter: A-Maze-ing → playable Level
│   ├── entities.py         Actor, Player, Ghost (movement + AI)
│   ├── game.py             the rules: score, lives, timer, levels, cheats
│   ├── highscores.py       top-ten table, safe load / atomic save
│   ├── render.py           the only pygame file (window, shapes, text, keys)
│   ├── ui.py               draws every screen
│   └── app.py              screen state machine + main loop
├── tests/                  pytest, runs headless (no window)
├── mazegenerator-2.1.0-…whl   the imposed generator, shipped as-is
├── Makefile                install / run / lint / test / package
├── build.sh, pacman.spec   PyInstaller packaging
├── .github/workflows/release.yml   CI: tests + builds for 3 OSes → Itch.io
└── project-management/     timeline, risks, choices, acceptance tests
```

---

### `constants.py`: shared vocabulary

Values used everywhere that the player cannot configure:

- **Window:** 1000×760 pixels, HUD 56 px high, 60 FPS.
- **Colours**, including one per ghost (Blinky red, Pinky pink, Inky cyan,
  Clyde orange).
- **Wall bits** of the generator: `NORTH=1`, `EAST=2`, `SOUTH=4`, `WEST=8`.
  `15` (all four walls) marks an isolated cell, which the generator uses to
  draw its "42" logo.
- **Enums:**
  - `Direction`: `UP=(0,-1)`, `DOWN`, `LEFT`, `RIGHT`, with `.delta` and
    `.opposite`.
  - `GhostState`: `CHASE`, `FRIGHTENED`, `EATEN`.
  - `Screen`: `MENU`, `HIGHSCORES`, `INSTRUCTIONS`, `PLAYING`, `PAUSED`,
    `LEVEL_CLEARED`, `NAME_ENTRY`, `ERROR`, `QUIT`.
  - `Tile`: `WALL`, `CORRIDOR`.

---

### `config.py`: a config file that cannot crash the game

#### Step 1: Strip the comments (`strip_json_comments`)

Standard JSON has no comments, so they are removed before `json.loads`.
It is a small character-by-character state machine:

- Outside a string: `#` and `//` blank out the rest of the line, and `/* */`
  blanks everything up to `*/`.
- Inside a string (between `"`): nothing is touched, so `"a#b.json"` survives.
  `\"` does not end the string.
- Comments are replaced with **spaces, and newlines are kept**, so when JSON
  reports *"error at line 12"* it is the real line 12 of the file.

#### Step 2: Validate every value

`parse_config` reads each key with a helper:

| Helper | Behaviour |
|---|---|
| `_as_int` / `_as_float` | missing → default; wrong type → default + warning; out of range → clamped + warning |
| `_as_bool` | only real `true` / `false` |
| `_as_filename` | non-empty string |

**Detail:** `isinstance(value, bool)` is checked first, because in Python
`True` *is* an `int`. Without that check, `"lives": true` would give 1 life.

#### Step 3: Levels

- `_parse_level` validates width and height (7–35), pacgum, max_time and
  ghost_speed. A level can override the global `pacgum` and `level_max_time`.
- `_parse_levels` **pads** to 10 levels if fewer are given, using `_grown`:
  each new level is 2 cells bigger and 0.2 tiles/s faster than the previous
  one.

The result is a **frozen** `GameConfig` dataclass, which holds only valid
values plus a list of `warnings`.

**Only two things raise `ConfigError`:** a file that cannot be read (or is not
`.json`), and JSON that is invalid after stripping. Everything else is
corrected.

---

### `maze.py`: the adapter around the imposed generator

This is the only file that knows `mazegenerator` exists. It treats the package
as **untrusted**.

#### `_instantiate`: probing the constructor

The package documentation and its code disagree on argument names, so several
signatures are tried in order:

```python
{"size": (w, h), "perfect": False, "seed": seed}
{"width": w, "height": h, "perfect": False, "seed": seed}
{"size": (w, h), "perfect": False}
{"size": (w, h)}
```

A `TypeError` means "wrong signature, try the next one". Any other exception
becomes a `MazeError`. The generator's stdout is silenced, because it prints a
cosmetic warning when the maze is too small for its "42" logo.

#### `_read_grid`: validating the output

It checks that `maze.maze` is a non-empty, rectangular list of integers (not
booleans). Otherwise it raises `MazeError`.

#### `_to_tiles`: cells → tiles

```
cell grid  w × h      →      tile grid  (2w+1) × (2h+1)

  cell (x, y)         →  tile (2x+1, 2y+1)     the cell centre
  wall east of it     →  tile (2x+2, 2y+1)     opened only if no wall
  wall south of it    →  tile (2x+1, 2y+2)     opened only if no wall
  even coordinates    →  walls / pillars       the border is always solid
```

A passage is opened only if **both** neighbouring cells agree there is no
wall, for example cell A has no EAST wall *and* cell B has no WEST wall. Trusting
only one side could punch holes through the maze. Fully closed cells (value 15,
the "42" logo) stay solid.

#### `_largest_component`: is everything reachable?

`perfect=False` can leave isolated pockets. A pacgum inside one would make the
level impossible to finish. A **flood fill** (iterative DFS with a stack) finds
every connected corridor group and keeps the biggest one. Everything is placed
inside it, so **every level is winnable** (a test checks this).

#### `_populate`: placing things

Using `_closest(candidates, target, taken)`, which finds the free tile nearest
to a target point:

1. Player → nearest to the centre.
2. 4 ghosts → nearest to each corner.
3. 4 super-pacgums → next nearest to each corner.
4. Pacgums → the remaining tiles, shuffled, cut to the configured count.

#### The random-seed trap

The generator calls `random.seed()` on Python's **global** random. If the game
used `random.random()` too, ghost behaviour would be tied to maze generation.
So the game only uses **private** `random.Random()` instances.

The result is a frozen `Level`: `tiles`, `player_spawn`, `ghost_spawns`,
`pacgums`, `super_pacgums` and `seed`, plus `is_wall(x, y)`, where off-grid
counts as a wall so no bounds check is ever needed.

---

### `entities.py`: movement and ghost AI

#### `Actor`: the movement model

An actor has:

```
tile        the tile it is leaving
next_tile   the tile it is entering
progress    0.0 → 1.0, how far along
direction, speed (tiles per second)
```

- `position` returns the **interpolated** position, which is used only for
  drawing and collisions.
- `update(delta, level, pick)`:
  1. If standing on a tile, ask `pick(self)` for a direction. If it is a wall
     or `None`, stand still.
  2. `progress += speed × delta`.
  3. When `progress ≥ 1`, arrive on `next_tile` and carry the leftover time
     into the next step (a `while` loop, so a fast actor can cross several
     tiles in one frame without skipping a wall check).
- `reverse()` swaps `tile` and `next_tile` and sets `progress = 1 − progress`,
  for an instant U-turn.

The **picker** pattern is a function passed in to choose the direction. The
movement code is shared, and only the decision differs between the player and
the ghosts.

#### `Player`

- Does not move until the first key press (`started`).
- `steer()`:
  - A **half-turn** is applied immediately (`reverse()`), which makes the
    controls feel responsive.
  - Any other turn is **buffered** in `desired` and applied at the next tile
    where it is possible. You can press ↑ before reaching a junction.
- Its picker: the desired direction if free, otherwise keep going straight,
  otherwise stop.

#### `Ghost`

States: `CHASE` → (super-pacgum) → `FRIGHTENED` → (eaten) → `EATEN` → (timer)
→ `CHASE`.

**`target()`**, the four personalities (taken from the arcade original):

| Ghost | Target tile |
|---|---|
| 0 Blinky | the player's tile, chasing directly |
| 1 Pinky | 4 tiles in front of the player, an ambush |
| 2 Inky | take the point 2 tiles in front of the player, then mirror Blinky through it (`2 × pivot − blinky`), a pincer |
| 3 Clyde | the player if more than 8 tiles away, otherwise his own corner (shy) |
| any, in scatter or frightened | its home corner |

**`picker()`:** at each tile, among the open directions **except going back**
(unless it is a dead end), take the one whose next tile is closest to the
target (squared distance). When frightened, the rule flips: maximise the
distance from the player. A tiny random term (`rng.random() × 0.1`) breaks
ties, so two ghosts do not move in lockstep.

#### `collides(player, ghost)`

True if both are within 0.6 tile on each axis. Eaten ghosts are ignored.

---

### `game.py`: the rules

`Game` holds one full run: `score`, `lives`, `level_index`, `status`
(`RUNNING` / `LEVEL_CLEARED` / `GAME_OVER` / `VICTORY`), `cheats`, `pacgums`
(a set of tiles), the player, the 4 ghosts and the timers.

Key methods:

| Method | Does |
|---|---|
| `_generate(i)` | builds level i; seed = config seed for level 0, random after |
| `_install_level()` | resets the pacgums, player, ghosts and timers, then shows "LEVEL n" |
| `update(delta)` | one simulation step (see Part 2, Step 4) |
| `_tick_timers` | level clock → `TIME UP`; frightened timer; scatter/chase alternation |
| `_collect` | pacgum / super-pacgum on the player's tile |
| `_resolve_contacts` | eat a ghost, or lose a life |
| `_lose_life(reason, restart)` | `lives -= 1`; at 0 → `GAME_OVER`; otherwise reset positions (and pacgums too if the time ran out) |
| `next_level()` | next level, or `VICTORY` after the last one; score and lives carry over |

Timing details:

- `READY_PAUSE = 1.5 s` freeze at the start of each life.
- While ghosts are frightened, the scatter/chase clock is **paused**.
- Ghost speed comes from each level's config, so later levels are faster.

**Cheats** (the `Cheats` dataclass): `toggle_invincible` (F1), `skip_level`
(F2), `toggle_frozen` (F3), `grant_life` (F4), `toggle_fast` (F5, ×1.8 speed),
`end_run` (F6). Each one sets `cheats.used = True`, and the score screen shows
that the run was cheated.

---

### `highscores.py`: the top ten

- `Entry(name, score)`, a frozen dataclass.
- `sanitize_name`: letters, digits and spaces only, at most 10 characters.
  Empty becomes `PLAYER`.
- `sanitize_score`: non-negative integers only (booleans rejected).
- `HighscoreTable.load()`: **never raises**.
  - Missing file → empty table, no warning (normal on a first run).
  - Unreadable, invalid JSON or not a list → empty table + warning.
  - Bad entries → dropped, the rest kept, + warning.
- `add()` → sort by score descending, keep 10.
- `save()`: **atomic write.** It writes to a temporary file in the same folder,
  then `os.replace()` it over the real file. A crash mid-write can never leave
  a half-written table. On failure (read-only folder, for example) it returns
  `False` with a warning, and the game continues.

Warnings are shown on the main menu.

---

### `render.py`: the only pygame file

A **facade**: `Display` exposes only basic primitives, each of which has an
MLX equivalent (MLX is the 42 graphics library):

| `Display` | MLX equivalent |
|---|---|
| `Display(w, h, title)` | `mlx_init` + `mlx_new_window` |
| `clear`, `rect` | `mlx_new_image` + `mlx_pixel_put` |
| `disc` | `mlx_pixel_put` over a disc |
| `text` | `mlx_string_put` |
| `present` | `mlx_put_image_to_window` |
| `poll` | `mlx_key_hook` + `mlx_hook` |
| `tick` | `mlx_loop_hook` |
| `close` | `mlx_destroy_window` |

**Porting to MLX means rewriting this one file.** No sprites, sounds or pygame
collision helpers are used.

Details:

- `tick()` returns the frame time **clamped to 0.05 s**. If the computer
  freezes for a second, a ghost moves 0.05 s worth, not a full second (which
  could teleport it).
- Only `display` and `font` are initialised, not `pygame.init()`. Starting the
  audio mixer on a machine without sound made the game hang for seconds at
  exit.
- Drawing goes into an off-screen buffer, then `present()` copies it to the
  window in one go (no flicker).
- `KeyPress(name, char)`: a key name independent of pygame (`"up"`, `"f1"`),
  plus the typed character for the name prompt.

---

### `ui.py`: every screen

These are pure drawing functions. They **read** the game state and call
`Display`, and they never change anything.

- `Viewport` + `viewport_for(level, display)`: computes the tile size so any
  maze size fits below the HUD and is centred. `to_pixels(x, y)` converts
  (fractional) tile coordinates to pixels, which is where the smooth movement
  appears.
- `draw_maze` (walls as a light edge + darker fill), `draw_pacgums`,
  `draw_player`, `draw_ghost` (body, eyes looking in the direction of movement,
  blue when frightened, **blinking white in the last 2 seconds**).
- `draw_hud`: score, lives, level n/12, time (red below 10 s), pacgums left,
  active cheats.
- Screens: `draw_menu`, `draw_highscores`, `draw_instructions`, `draw_pause`,
  `draw_level_cleared`, `draw_name_entry`, `draw_error`.

---

### `app.py`: the state machine

The app is always on exactly one `Screen`. Each screen has its own key handler,
stored in a dictionary:

```
MENU ──Start──▶ PLAYING ──P/Esc──▶ PAUSED ──Resume──▶ PLAYING
 │  ▲              │                  └──Menu──▶ MENU
 │  │              ├──all pacgums──▶ LEVEL_CLEARED ──Enter──▶ PLAYING (next level)
 │  │              │                                   └─last level─▶ NAME_ENTRY
 │  │              └──no lives──▶ NAME_ENTRY ──Enter (save)──▶ MENU
 │  └── Esc/Enter ── HIGHSCORES / INSTRUCTIONS / ERROR
 └──Esc / Exit──▶ QUIT
```

- `_on_playing_key`: arrows/WASD → `steer`, P/Esc → pause, F1–F6 → cheats (if
  `cheats_enabled`).
- A `MazeError` while starting or advancing a level → `ERROR` screen, not a
  crash.
- `run_game()` closes the display in `finally`.

---

### `pac-man.py`: the entry point

| Situation | Result |
|---|---|
| 0 or more than 1 arguments | message + usage, exit 1 |
| Not `.json` / unreadable / invalid JSON | `error: …` with the line number, exit 1 |
| Out-of-range values | warnings on stderr, game runs |
| No display available | `error: cannot open a game window`, exit 1 |
| Ctrl+C | `interrupted`, exit 130 |

`bundled_config()`: in the packaged (PyInstaller) build, the game starts with no
argument and uses the `config.json` next to the executable, or the embedded
copy otherwise.

---

### `tests/`: what is checked

| File | Checks |
|---|---|
| `test_config.py` | all comment styles; markers inside strings survive; line numbers preserved; `{}` gives defaults; clamping; wrong types; `true` is not a number; level padding; overrides; clean errors |
| `test_maze.py` | grid is 2w+1; solid border; same seed = same maze; spawns on corridors; **everything reachable** (several sizes × seeds); 4 super-pacgums near corners; missing generator handled; no stdout leak |
| `test_game.py` | movement maths; walls stop actors; instant U-turn; buffered turns; ghosts chase / flee / never turn back; respawn; scoring; lives; timer; level progression; every cheat; **property tests: score never decreases, the player never enters a wall, positions stay in bounds** over simulated random play |
| `test_highscores.py` | name and score sanitising; missing / corrupt / wrong-shape files; bad entries dropped; sorted and capped; round-trip; save failure reported |

109 tests in total (some are parametrised). They all run **without a window**,
which is only possible because the rules do not depend on pygame.

---

### Packaging and CI

- `build.sh` + `pacman.spec`: PyInstaller freezes the game into one executable,
  copies `config.json` next to it, and zips it into `dist/`.
- `.github/workflows/release.yml`: runs lint + tests, then builds on Linux,
  Windows and macOS runners (PyInstaller cannot cross-compile), and pushes each
  build to Itch.io with `butler`. It is triggered manually or by a `v*` tag.

---

## Part 4: Design decisions and why

| Decision | Why |
|---|---|
| **Rules separated from drawing** | Testable without a display; the UI cannot corrupt the state |
| **Tile-based movement with interpolation** | Smooth on screen, but never inside a wall; collisions cannot be skipped between frames |
| **pygame confined to `render.py`** | The backend is replaceable (MLX port = one file); only primitives MLX also has |
| **Adapter around the generator** | It must stay unmodified, its docs and code disagree, and it can fail, so all of that is contained in one file |
| **Flood fill before placing pacgums** | `perfect=False` can create unreachable pockets, which would make a level unwinnable |
| **Private `random.Random` instances** | The generator reseeds the global `random` |
| **Clamp config values instead of refusing them** | A typo should not stop the game; the player is told what was fixed |
| **Atomic highscore save** | An interrupted write can never destroy the existing table |
| **Clamp the frame time to 0.05 s** | A lag spike cannot teleport an actor through a wall |
| **Frozen dataclasses** for `GameConfig`, `Level`, `Entry` | Validated once, then nobody can change them by accident |

---

## Part 5: Questions you will probably be asked

**Q: How do you use the maze generator without modifying it?**
Only `maze.py` imports it. It tries several constructor signatures, validates
what comes back, and converts its cells-with-wall-bits into a tile grid.
Nothing is patched or subclassed.

**Q: Why is a 15×15 maze 31×31 on screen?**
The generator stores walls *between* cells. Pac-Man needs walls that *are*
squares, so each cell plus its east and south walls becomes 2×2 tiles, plus
one border row and column: `2 × 15 + 1 = 31`.

**Q: How do you guarantee every level can be finished?**
A flood fill keeps only the largest connected corridor area, and everything is
placed inside it. A test checks it over four sizes and three seeds.

**Q: How do the ghosts decide where to go?**
Each computes a target tile (its personality). At every tile it picks the open
direction, excluding going back, whose next tile is closest to that target.
That is a greedy choice, not pathfinding, just like the arcade original.

**Q: Why not use A\* / BFS for the ghosts?**
Perfect pathfinding makes the ghosts unbeatable and all identical. The
greedy-target rule gives each ghost a recognisable personality and leaves the
player room to escape, as in the original game.

**Q: What happens if two keys are pressed before a junction?**
The latest one is kept in `desired` and applied at the first tile where that
direction is open.

**Q: What happens if the config file is broken?**
Broken JSON → a one-line error with the line number, exit 1. Valid JSON with
bad values → each value is replaced or clamped, a warning is printed, and the
game starts.

**Q: What if `highscores.json` is corrupt?**
The game starts with an empty (or partial) table and shows a warning. It never
crashes.

**Q: Why is level 1 always the same?**
It uses the `seed` from the config, so it is reproducible for testing and
review. Later levels use random seeds.

**Q: How would you port it to MLX?**
Rewrite `render.py` only. The module docstring maps each `Display` method to
its MLX function.

**Q: Why is the ghost speed lower than the player's?**
Default player 6.0 vs ghosts 4.5 tiles/s, so the player can escape. Later
levels raise the ghost speed in `config.json`.

**Q: How did you test a game without playing it?**
The rules are pure Python in tiles and seconds. Tests build a `Game`, call
`update()` with fixed time steps, and check the state, including property tests
over two simulated minutes of random play.

**Q: Did you use AI?**
Yes, as a pair-programming assistant: design discussion, first drafts of the
config loader, the drawing code and the tests, debugging (the exit freeze
caused by the audio mixer), and documentation. Everything was reviewed and
reworked by hand. The maze adaptation, level balance and movement model needed
the most human decisions. (See the README section *Use of AI*.)

---

## Glossary

| Term | Meaning |
|---|---|
| **Cell** | One square of the *generator's* grid; it stores 4 wall bits |
| **Tile** | One square of the *game's* grid; either a wall or a corridor |
| **Wall bits** | `N=1, E=2, S=4, W=8`; a cell value is their sum (15 = closed) |
| **Perfect maze** | Exactly one path between any two points (no loops). Here `perfect=False`, so it has loops, which Pac-Man needs |
| **Flood fill** | Spreading from one tile to every connected tile to find a reachable area |
| **Actor** | Anything that moves: the player or a ghost |
| **Picker** | The function that decides an actor's next direction at each tile |
| **Interpolation** | Drawing an actor between two tiles according to `progress` |
| **Scatter / Chase** | Ghost phases: retreat to the corners (7 s) / hunt (20 s) |
| **Frightened** | After a super-pacgum: ghosts are blue, edible, and flee |
| **Delta (`delta`)** | Seconds elapsed since the previous frame |
| **Facade** | A small interface hiding a bigger library (here, pygame) |
| **State machine** | The app is always in exactly one `Screen`, and keys move it between screens |
| **Atomic write** | Write to a temporary file, then rename it, so the file is never half-written |
| **Clamping** | Forcing a value into its allowed range (e.g. `lives: 500` → 99) |
