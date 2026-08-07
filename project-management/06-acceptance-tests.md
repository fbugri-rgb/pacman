# Acceptance test plan

This is the checklist run before a defense. Every case is manual unless
it says otherwise, takes a couple of minutes, and maps to a requirement
of the subject. The automated suite (`make test`) covers the logic
underneath; this plan covers what a reviewer actually sees.

Preconditions: a clean machine, `make install` done, the A-Maze-ing
wheel installed from the repository, no highscore file present.

## A. Launch and command line

| # | Steps | Expected |
| --- | --- | --- |
| A1 | `python3 pac-man.py config.json` | The main menu opens |
| A2 | `python3 pac-man.py` | One-line error, usage line, exit code 1, no traceback |
| A3 | `python3 pac-man.py a.json b.json` | One-line error about the argument count, exit code 1 |
| A4 | `python3 pac-man.py config.txt` | Refused because the extension is not `.json`, exit code 1 |
| A5 | `python3 pac-man.py missing.json` | Clear "cannot be read" message, exit code 1 |
| A6 | `make run`, `make debug`, `make clean`, `make lint`, `make test` | Each rule does what its name says; `lint` and `test` report nothing |

## B. Configuration robustness

The reviewer is expected to edit `config.json` here. Every case must
start the game and print what was corrected.

| # | Steps | Expected |
| --- | --- | --- |
| B1 | Keep only `{}` in the file | Game runs on ten default levels, warnings listed on stderr |
| B2 | Add `# comment` lines, `// comment` and `/* block */` | All accepted, values unchanged |
| B3 | Put a comment marker inside a string, e.g. a filename `a#b.json` | Kept verbatim, not stripped |
| B4 | `"lives": -7` | Clamped to 1, one warning naming `lives` |
| B5 | `"lives": "three"` or `"lives": true` | Falls back to the default, one warning |
| B6 | `"width": 1`, `"height": 9999` on a level | Clamped to the documented bounds, warnings |
| B7 | Add `"totally_unknown": 12` | Ignored silently, game runs |
| B8 | Provide a single level entry | Padded to the ten mandatory levels |
| B9 | Break the JSON on purpose, e.g. `{"lives": }` | One-line error with the line number, exit code 1, no traceback |
| B10 | Change `seed` | The first level differs from the previous run and is reproducible across runs |
| B11 | Change `points_per_pacgum`, `points_per_ghost` | The HUD score follows the new values |
| B12 | Change `level_max_time` | The HUD timer starts from the new value |

## C. Maze generation

| # | Steps | Expected |
| --- | --- | --- |
| C1 | Reinstall the wheel from the repository, then start a game | Works with no code change; the package is untouched |
| C2 | Start the same seed twice | Identical first level |
| C3 | Reach level 2 and above (F2 to skip) | Each level is a new random maze, larger than the previous one |
| C4 | Look at the board | Solid outer border, player in the middle, one ghost per corner, four super-pacgums near the corners, pacgums filling the corridors |
| C5 | Automated: `make test` | No collectible outside the area reachable from the player spawn, over four sizes and three seeds |
| C6 | Uninstall the generator, then start a game | Error screen saying the package is not installed, no traceback |

## D. Gameplay

| # | Steps | Expected |
| --- | --- | --- |
| D1 | Press an arrow key, then W A S D | The player moves in the four directions with either set |
| D2 | Steer into a wall | The player stops, never crosses it |
| D3 | Ask for a turn slightly before a junction | The turn is applied at the junction, not lost |
| D4 | Press the opposite direction while moving | Immediate half-turn |
| D5 | Eat pacgums | Score increases, dots disappear, the counter in the HUD goes down |
| D6 | Eat a super-pacgum | Ghosts turn blue, flee, and blink before the end of the effect |
| D7 | Eat a fleeing ghost | Score increases, the ghost leaves the board and comes back to its corner after a delay |
| D8 | Get touched by a hunting ghost | One life lost, both the player and the ghosts return to their spawns, the level is not restarted |
| D9 | Lose the last life | Game over screen with the final score and a name prompt |
| D10 | Let the timer expire | One life lost and the level restarts with its pacgums back |
| D11 | Eat every pacgum | Level cleared screen, then the next level with the score and lives kept |
| D12 | Watch a ghost for a while | It hunts, and periodically retreats towards its corner; the four ghosts do not follow the same path |
| D13 | Play for several minutes | The score never decreases |

## E. Interface

| # | Steps | Expected |
| --- | --- | --- |
| E1 | Main menu | Start Game, View Highscores, Instructions, Exit; arrows move, Enter validates |
| E2 | HUD during play | Score, lives, level number and remaining time all visible and live |
| E3 | Press `P` or `Esc` while playing | The game freezes; resume and return to the main menu are both offered |
| E4 | Resume | The run continues exactly where it stopped, timer included |
| E5 | Return to the main menu from the pause | The run is dropped, the menu is shown |
| E6 | Instructions screen | Controls and cheat keys listed, Esc goes back |
| E7 | Finish the last level | Victory screen with congratulations, the final score and a name prompt |

## F. Highscores

| # | Steps | Expected |
| --- | --- | --- |
| F1 | Finish a run and type a name | Score saved, table shown sorted |
| F2 | Type more than ten characters, and symbols like `<>!/` | Truncated to ten, symbols refused, letters, digits and spaces kept |
| F3 | Validate an empty name | A default name is used |
| F4 | Restart the game, open View Highscores | The table survived the restart |
| F5 | Fill more than ten entries | Only the ten best remain, in decreasing order |
| F6 | Corrupt the file with random text, restart | Empty table plus a warning, no crash |
| F7 | Replace the file with a directory of the same name, finish a run | The save failure is reported in the interface, the game stays usable |

## G. Cheat mode (peer review)

| # | Steps | Expected |
| --- | --- | --- |
| G1 | `F1` then walk into a ghost | No life lost |
| G2 | `F2` | The current level is cleared immediately |
| G3 | `F3` | The ghosts stop moving; pressing it again frees them |
| G4 | `F4` | One more life in the HUD |
| G5 | `F5` | The player moves visibly faster; pressing it again restores the speed |
| G6 | `F6` | The run ends and goes to the score screen |

## H. Robustness and quality

| # | Steps | Expected |
| --- | --- | --- |
| H1 | Whole session, all screens | No traceback ever printed |
| H2 | `Ctrl+C` in the terminal while playing | Clean exit, one message, code 130 |
| H3 | Close the window with the title bar button | Clean exit, code 0, no freeze |
| H4 | `make lint` and `make lint-strict` | Nothing reported by flake8 or mypy |
| H5 | `make test` | All tests pass |
| H6 | Resize considerations: run a small level and level 12 | The board scales to fit the window in both cases |

## I. Packaging

| # | Steps | Expected |
| --- | --- | --- |
| I1 | `./build.sh` from a clean tree | A zip is produced under `dist/` |
| I2 | Unzip elsewhere and run the binary with no argument | The game starts on the bundled configuration |
| I3 | Edit the `config.json` shipped next to the binary, run it again | The change is taken into account, since that file wins over the embedded copy |
| I4 | Download the build from the store page and run it | Same behaviour as the local build |
