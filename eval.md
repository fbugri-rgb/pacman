# Pac-Man — evaluation dry run

Dry run of the official 42 scale (`pac-man-eval-sheet.pdf`) against this
repository, done on 2026-10-30.

**Method**

- `git clone` from vogsphere into an empty folder, with a fresh venv and `make install`.
- The game was driven headlessly (`SDL_VIDEODRIVER=dummy`) through a script
  that injects key presses into the real `App` loop. It covers the full game
  cycle and 240,000 frames of random keys.
- The config and the highscore file were fuzzed with hostile values.
- Every maze size from 7×7 to 35×35 was generated with 3 seeds.
- The package was rebuilt with `make package` and the binary was run.

Not checked here, because they need a person at the keyboard: how the game
looks and feels to play, `make debug` (interactive pdb), and the evaluator
downloading from Itch.io.

---

## 1. Results before fixes

| # | Scale item | Result | Evidence |
|---|---|---|---|
| 1 | Preliminaries | ✅ | All required files are present. The vogsphere `main` was 1 commit behind GitHub (`explanation.md` not pushed). |
| 2 | Project management | ✅ | `project-management/` holds 7 documents (≈5,000 words): timeline/Gantt/Kanban, progress, analysis & choices, risks, organisation, acceptance tests, blocking points. |
| 3 | README.md | ✅ | Italic credit on the first line. Description, Instructions, Resources (+ AI use), Configuration, Highscore, Maze generation, Implementation, Architecture, Project management. |
| 4 | Makefile | ✅ | `install`, `run`, `debug`, `clean` and `lint` are present, plus `lint-strict`, `test`, `package`, `fclean` and `re`. |
| 5 | Code quality | ✅ | `make lint` → flake8 clean, mypy "no issues in 15 files". `make lint-strict` (`mypy --strict`) is also clean. 109/109 pytest. |
| 6 | Usage (CLI) | ✅ | 0 or 2 arguments, a missing file, a directory, a non-`.json` file, an empty file, a top-level array and invalid UTF-8 all give a one-line message and exit code 1. `make run` → `python3 pac-man.py config.json`. |
| 7 | Configuration file | ✅ | `#`, `//` and `/* */` comments work. Wrong types or out-of-range values are clamped with a warning. Unknown keys are ignored. Fewer than 10 levels are padded. |
| 8 | **Error handling** | ❌ | **Tracebacks found**, see §2. |
| 9 | Build and run | ✅ | Works through the README steps and through `make run`. |
| 10 | Main menu | ✅ | Start Game / View Highscores / Instructions / Exit. |
| 11 | Level structure | ✅ | Level 1 uses seed 42 and is deterministic (two builds compared equal). Ghosts start in the 4 corners, super-pacgums sit next to them, the player starts in the centre, pacgums fill the corridors. |
| 12 | Player mechanics | ✅ | The player moves and is blocked by walls. A ghost caught it after about 16 s idle, the lives went 3 → 2 and it respawned at the centre spawn. |
| 13 | Ghosts mechanics | ✅ | Each ghost has its own chase target. They flee while edible. An eaten ghost leaves the board and comes back to its corner after `ghost_respawn_delay`. |
| 14 | Pacgum / super-pacgum | ✅ | +10 / +50. All 4 ghosts become edible for 8 s, then go back to normal. |
| 15 | Scoring | ✅ | +200 per ghost. The score is shown in the HUD and never goes down. |
| 16 | Cheat mode | ✅ | F1 invincible, F2 skip level, F3 freeze ghosts, F4 +1 life, F5 speed, F6 end run. Active cheats are shown in the HUD and flagged on the score screen. |
| 17 | Game progression | ✅ | 10 levels → VICTORY → name entry → menu. Running out of time costs a life and restarts the level. Pause freezes the timer. Pause → "main menu" works. |
| 18 | Highscore persistence | ✅ | Empty table → finish a run → enter a name → quit → restart → the entry is still there. Names are capped at 10 alphanumeric/space characters ("Eval Bot!!xyz" → "Eval Botxy"). |
| 19 | User interface | ✅ | HUD: score, lives, level n/N, time, gums left. Pause: resume / main menu. Game over and victory screens show the final score and a name prompt. |
| 20 | Maze generator integration | ✅ | The repo wheel's sha256 is identical to the wheel inside the official `mazegenerator-00001.zip`. Every call goes through `pacman/maze.py`. `perfect=False`. Generator errors become `MazeError` → error screen. 2,523 sizes/seeds generated without a failure. |
| 21 | OOP | ✅ | `Actor` → `Player` and `Ghost`. The wall rule (`open_directions`) lives in `Actor`, so both inherit it. `Game`, `App`, `Display`, `HighscoreTable` and `Level` are separate classes. |
| 22 | Packaging & platform | ⚠️ | `make package` rebuilds `dist/pac-man-linux.zip` (binary + config + README) and the binary runs. **The Itch.io page is public**, while the subject asks for an unlisted/private build. |

## 2. Issues found

| ID | Severity | Issue | Reproduction |
|---|---|---|---|
| E1 | **Crash flag (grade 0)** | Non-finite numbers in the config crash the loader (`int(inf)` / `int(nan)`). | `{"lives": 1e999}` or `{"seed": NaN}` → `OverflowError` / `ValueError` traceback |
| E2 | **Crash flag (grade 0)** | Non-finite scores in the highscore file crash the game at startup. | `highscores.json` = `[{"name":"a","score":1e999}]` → traceback |
| E3 | **Crash flag (grade 0)** | A deeply nested JSON document crashes the config loader. | config = `[[[[…` (100k) → `RecursionError` traceback |
| E4 | Medium | NaN in a float key is accepted silently: both range checks are false for NaN, so it gets through. | `{"super_pacgum_duration": NaN}` → no warning |
| E5 | Medium | Same as E3 for the highscore file (`RecursionError` was not caught). | highscore file = `[[[[…` |
| C1 | Cosmetic | A missing `level` prints two contradictory warnings: "no level defined; generating 10" and "only 1 level(s) defined". | `{}` |
| C2 | Cosmetic | The main menu shows only `warnings[0]`, so a failed highscore save was hidden behind any config warning. Highscore warnings are not printed on stderr either. | unwritable `highscore_filename` + any config warning |
| C3 | Cosmetic | `setup.cfg` excludes `.venv/` and `venv/` but not `env/`, so an evaluator venv named `env` would be linted. | `python3 -m venv env && make lint` |
| P1 | **Mandatory** | The Itch.io page is public; the subject requires unlisted/private. | <https://fbugri-rgb.itch.io/pacman> returns 200 with 3 public uploads |
| P2 | Check | The eval sheet lists repo `intra-uuid-178f2cdb-…`, but the `vogsphere` remote is `intra-uuid-7a6caa5d-…-fbugri`. | Compare with `git remote -v` |
| P3 | Minor | `explanation.md` (commit `2ef5b6a`) is on GitHub but not on vogsphere. | `git log vogsphere/main..main` |

---

## 3. Changes made to the code

All the code issues (E1–E5, C1–C3) are fixed. P1–P3 are outside the code
and listed in §4.

### `pacman/config.py` — fixes E1, E3, E4, C1

- **`_as_int`**: a `float` that is `inf` or `nan` is rejected before
  `int()` is called. It gets the warning `'<key>': inf is not a finite
  number; using <default>.` and falls back to the default.
- **`_as_float`**: the same check runs after `float()`, so NaN can no
  longer slip past the range test.
- **`parse_config`**: `RecursionError` from `json.loads` becomes
  `ConfigError("the config is nested too deeply")`, printed as a one-line
  `error:` with exit code 1. The docstring `Raises:` section is updated.
- **`_parse_levels`**: the "no level defined" warning is now emitted only
  when the level list is really empty. "only N level(s) defined" is
  emitted only when some levels exist (`elif`). A non-array `level` now
  says "expected an array; ignoring it." instead of a third message about
  generating defaults. Padding behaviour is unchanged.

### `pacman/highscores.py` — fixes E2, E5

- **`sanitize_score`**: `inf` and `nan` return `None`, so that record is
  dropped and counted in the "ignored N malformed entries" warning.
- **`HighscoreTable.load`**: `RecursionError` is added to the caught
  exceptions, so the game starts with an empty table and a warning.

### `pacman/app.py` — fixes C2

- **`App.warnings`** now returns the highscore warnings first, newest
  first, then the config warnings. The single warning line on the main
  menu therefore shows a failed save right after it happens, instead of a
  config message that was already printed on stderr at startup.

### `setup.cfg` — fixes C3

- `env` is added to the flake8 `exclude` list.

### Tests — 6 new, 115 in total

- `tests/test_config.py`
  - `test_non_finite_numbers_fall_back_to_defaults`: `1e999`, `NaN`,
    `Infinity` and `-Infinity` in global and per-level keys.
  - `test_missing_levels_are_reported_once`
  - `test_deeply_nested_json_raises_config_error`
- `tests/test_highscores.py`
  - `test_score_rejects_non_finite_numbers`
  - `test_non_finite_scores_are_dropped`
  - `test_deeply_nested_file_is_recovered`

### Verification after the changes

| Check | Result |
|---|---|
| `make lint` | flake8 clean, mypy: no issues in 15 files |
| `make lint-strict` | no issues in 15 files |
| `make test` | 115 passed |
| E1–E5 reproductions | no traceback: clean warning or `error:` line, or the game starts normally |
| Headless full cycle + 240k-frame fuzz + 2,523 maze generations | no exception, same behaviour as before |
| Broken highscore path (`/etc`) | the menu shows the highscore read error, then the write error after a save |

`git diff --stat`: `pacman/app.py`, `pacman/config.py`,
`pacman/highscores.py`, `setup.cfg`, `tests/test_config.py`,
`tests/test_highscores.py`. Nothing is committed yet.

---

## 4. Still to do (outside the code)

1. **Itch.io → Restricted (P1).** Set the visibility on itch.io to
   *Restricted*, not *Draft*, so the evaluator can still download it
   through the secret URL. The README already says "unlisted build".
2. **Confirm the graded repository (P2).** Check which vogsphere repo the
   evaluator clones (`intra-uuid-178f2cdb-…` on the sheet). Make sure it
   holds the final code.
3. **Commit and push to vogsphere (P3).** This includes these fixes and
   `explanation.md`. Then re-clone into an empty folder and re-run
   `make install && make lint && make run` once.
4. **Ready-to-explain points for the defense:**
   - **Corners:** ghosts take the exact corners and super-pacgums take the
     nearest free tile, because the subject puts both in "the 4 corners".
   - **Maze generator:** `maze.py` tries several constructor signatures.
     The package's docs and its code disagree.
   - **Time limit:** running out of time costs a life and restarts the
     level. The subject leaves this choice open.
   - **OOP:** the "can't cross walls" rule is inherited from `Actor`.
