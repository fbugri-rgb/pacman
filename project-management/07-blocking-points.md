# Blocking points

The problems that actually cost time, what they turned out to be, and
what was changed so they cannot come back.

## B1 — The generator's documented constructor is not the real one

**When:** work package 3, cost about half a day, and made M2 one day
late.

The package README shows a constructor taking `width` and `height`, but
the shipped code only accepts a `size` couple. The subject forbids
touching the package, and the wheel is reinstalled by the reviewer, so
neither patching it nor hard-coding one spelling was acceptable.

**Resolution:** the loader tries several plausible constructor
signatures in order and keeps the first that is accepted, then reads the
grid through the public properties only. If a future version of the
package changes its keywords again, the loader adapts instead of
crashing; if none works, the failure is reported as a clean error.

## B2 — The generator seeds the global random source

**When:** work package 3, half an hour, but it would have been very hard
to diagnose later.

Calling the generator reseeds Python's global `random` module. Anything
else drawing from that source — the ghost tie-breaking, the placement of
collectibles — would then have become correlated with the maze seed, and
two different levels could have produced identical ghost behaviour.

**Resolution:** the game never uses the module-level functions of
`random`; it owns private `random.Random` instances. The global source
belongs to the generator and to nobody else.

## B3 — Non-perfect mazes contain unreachable pockets

**When:** work package 3, discovered while checking the first generated
boards.

With `perfect = False`, which the subject requires, the grid can contain
corridor cells with no path to the player. A pacgum placed there makes
the level impossible to finish. The bug is invisible most of the time
and would surface exactly once, during a defense.

**Resolution:** a flood fill from the player spawn computes the reachable
area, and every collectible and every ghost spawn is placed inside it.
A test asserts the property across four maze sizes and three seeds.

## B4 — Sixteen-second freeze when closing the window

**When:** work package 6, about an hour, most of it spent suspecting the
game loop.

Quitting took roughly sixteen seconds on a machine without a sound card.
The game has no sound at all, so nothing pointed at audio.

**Resolution:** the culprit was the blanket initialisation of pygame,
which starts the audio mixer; shutting it down blocks when there is no
audio device. Only the video and font subsystems are started now, and
they are the only ones shut down. Exit is instant. The reason is written
down in the code, because the fix looks arbitrary otherwise.

## B5 — Time limits that made levels unwinnable

**When:** work package 5, and it changed the shipped configuration.

Pacgums are spread over the whole maze, so clearing a level requires
walking through almost every corridor whatever the number of dots. The
first configuration used large mazes with round time limits, and the
later levels simply could not be finished.

**Resolution:** the level table was rebuilt from a measurement instead of
a guess — the time limit of a level is derived from its corridor count
divided by the player speed, with a margin. The maze sizes were reduced
accordingly, and every corridor is filled with a pacgum so that the
player can see at a glance what is left.

## B6 — A false alarm worth recording

**When:** work package 4, twenty minutes.

An automated run reported that the player never moved and the score
stayed at zero. The suspicion fell on the movement code.

**Resolution:** nothing was broken. The test steered the player into a
wall, because the spawn tile of that particular maze only opens upwards
and downwards. The lesson kept: before debugging, check that the test
itself asks for something possible. Two tests of the final suite were
wrong for exactly this reason and were fixed rather than the code.
