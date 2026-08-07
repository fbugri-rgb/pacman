# Risk analysis

Risks are scored on likelihood and impact from 1 (low) to 3 (high). The
score is their product; anything at 6 or above got a mitigation
implemented in the code rather than a note in a document.

| # | Risk | L | I | Score | Mitigation | State |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | The imposed generator behaves differently once reinstalled by the reviewer | 2 | 3 | 6 | The loader probes the constructor signature instead of assuming one, and reads the grid through the public properties only. No file of the package is modified or vendored. | mitigated |
| R2 | The generator raises or returns an unusable grid | 2 | 3 | 6 | Every call is wrapped and converted into `MazeError`, caught by the application, which shows an error screen instead of crashing. | mitigated |
| R3 | A level is unwinnable because pacgums land in an unreachable pocket | 2 | 3 | 6 | `perfect = False` allows pockets, so collectibles are placed only on the connected component of the player spawn. Covered by a test over four sizes and three seeds. | mitigated |
| R4 | The replacement configuration used at the defense breaks the game | 3 | 3 | 9 | Every field is type-checked and clamped, unknown keys are ignored, missing keys fall back to documented defaults, and every correction is printed. The empty object `{}` is a valid configuration. | mitigated |
| R5 | A traceback reaches the terminal, an automatic failure | 2 | 3 | 6 | Three domain exceptions (`ConfigError`, `MazeError`, `DisplayError`), a single catch point in the entry script, and a display facade that converts backend failures. Windows are closed through context management. | mitigated |
| R6 | The time limit makes levels unfinishable, or trivial | 3 | 2 | 6 | Time limits are derived from the corridor count and the player speed with a measured margin, and rechecked whenever the level sizes change. | mitigated |
| R7 | The game runs at a different speed on a faster or slower machine | 2 | 3 | 6 | All movement is expressed in tiles per second and multiplied by the real frame delta, which is also clamped so that a long stall cannot teleport an actor through a wall. | mitigated |
| R8 | pygame is unavailable or the machine has no display | 2 | 2 | 4 | The import failure is reported as a clear message; only the video and font subsystems are initialised, never audio, which also avoids a several-second freeze at exit on machines without a sound card. | mitigated |
| R9 | The highscore file is corrupt, unreadable or on a full disk | 2 | 2 | 4 | Corrupt content yields an empty table plus a warning; writes go through a temporary file and an atomic rename; a failed save is reported in the interface, not fatal. | mitigated |
| R10 | The frozen build behaves differently from the sources | 2 | 2 | 4 | The configuration is bundled *and* copied next to the binary, and the packaged game falls back to the bundled file when started with no argument. The build script is rerunnable from a clean tree. | mitigated |
| R11 | Solo project: no one else can take over if the author is unavailable | 2 | 3 | 6 | Scope kept strictly at the mandatory requirements, every module documented, and the whole state of the project reconstructible from the repository alone. | accepted |
| R12 | Time spent on graphics polish instead of mandatory features | 3 | 2 | 6 | Cosmetic ideas were pushed to the backlog column of the board and none was started before M4. | mitigated |

## Residual risk

R11 is accepted rather than mitigated: with one person, there is no
redundancy to buy. The exposure is limited by keeping the scope small
and the repository self-explanatory, which is the only lever available.
