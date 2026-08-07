# Organisation

## Team

The project is done solo, by **fbugri**. There is therefore no work
split to arbitrate, but the roles still exist and were kept separate in
time, because doing them at once is how a solo project ends up with code
that only its author can run:

| Role | What it covers | When |
| --- | --- | --- |
| Architect | Module boundaries, choice of the rendering facade, data model | Before each work package |
| Developer | Implementation | Daily |
| Reviewer | Reading yesterday's code before writing new code | Start of each session |
| Tester | Acceptance plan, test suite, headless runs | End of each work package |
| Release manager | Packaging, documentation, defense rehearsal | M5 |

## Working rules

- **The linters are part of the build, not a final step.** `make lint`
  runs before every commit; a red lint is treated like a broken build.
- **One work package at a time.** A package is finished when it is
  demonstrable, not when the code is written.
- **Ideas go to the backlog, not into the branch.** Anything outside the
  mandatory requirements is written on the board and left there.
- **No requirement is trusted from memory.** Each work package started
  by rereading the paragraph of the subject that covers it; the
  requirement checklist in
  [06-acceptance-tests.md](06-acceptance-tests.md) is the trace of that.
- **The generator is read-only.** Its wheel stays in the repository as
  shipped, and is reinstalled from scratch to check that nothing local
  is being relied on.

## Tooling

| Need | Tool |
| --- | --- |
| Language | Python 3.10 |
| Display | pygame, confined to `pacman/render.py` |
| Maze | the imposed A-Maze-ing package, unmodified |
| Style | flake8 |
| Types | mypy, with the subject flags and with `--strict` |
| Tests | pytest, runnable headless |
| Packaging | PyInstaller through `pacman.spec` and `build.sh` |
| Automation | `make` |

## Communication

Solo, so no meetings. The board in
[01-timeline.md](01-timeline.md) and this directory play the role of the
shared memory: they are what a reviewer, or the author three months
later, reads first.
