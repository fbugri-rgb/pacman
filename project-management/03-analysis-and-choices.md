# Analysis and technical choices

## Reading of the subject

Three requirements shape the whole design, because they constrain every
module rather than one feature:

1. **The maze generator is imposed and must stay untouched.** Its
   interface is the only fixed point of the project; the loader adapts to
   it. It is also reinstalled by the reviewer, so nothing may depend on a
   local edit or on a cached copy.
2. **No traceback may reach the terminal.** This is not an error-handling
   detail added at the end, it decides where the boundaries of the
   program are: file access, JSON parsing, the generator call and the
   display are the four places where the outside world can misbehave, and
   each converts failures into a domain exception.
3. **The configuration is replaced during the defense.** Every value read
   from it is therefore hostile input: wrong type, absurd range, missing
   key, unknown key. The loader clamps and reports, never crashes and
   never trusts.

The rest of the subject is classic gameplay work, and it is the part with
the fewest surprises.

## Decisions

### Language level and typing

Python 3.10 with `from __future__ import annotations` everywhere. The
subject asks for the flag set of `make lint`; the project also passes
`mypy . --strict`, which additionally forbids untyped call sites and
implicit `Any`. Passing the stricter set costs almost nothing when
started on day one, and it caught two real defects: an optional value
that could reach the drawing code as `None`, and an enum member reached
through an instance instead of through its class.

### Rendering isolated behind one module

`pacman/render.py` is the only file that imports pygame. Everything else
draws through a small facade of rectangles, discs, text and key events.
This is a direct answer to the subject's hint about MLX: the facade uses
only primitives that MLX also offers, and the module docstring carries
the correspondence table. A port would rewrite one file of the eight.

The alternative — calling pygame from the UI code — would have been
shorter to write and would have tied the game to one library forever.

### Tile grid with continuous interpolation

Actors store the tile they leave, the tile they enter and a progress
between the two. Movement is smooth on screen, but every decision (turn,
collision, pacgum eaten) happens exactly on a tile boundary. This
removes an entire class of bugs: an actor can never be halfway inside a
wall, and a collision cannot be missed between two frames because both
actors are compared in tile space.

The rejected alternative was free pixel movement with rectangle
intersection, which is what most naive Pac-Man clones do and which makes
corner turns feel imprecise.

### Ghost behaviour

Rather than four copies of the same chase, the ghosts reproduce the
arcade personalities: direct chase, ambush four tiles ahead, mirrored
target through the red ghost, and a shy one that retreats when it comes
too close. A scatter phase alternates with the chase phase, and a ghost
never reverses at a junction. The result is that the four ghosts spread
out naturally and the player is never surrounded by a single blob, which
is the actual reason the original design exists.

### Configuration format

The subject requires JSON *with comments*, which no standard parser
accepts. The chosen approach is a character scanner that blanks the
comments while preserving line numbers, then hands the result to the
standard `json` module. Preserving line numbers matters: a syntax error
is reported at the line the user actually wrote. Writing a full JSON
parser by hand was rejected as needless risk.

### Reachability guarantee

The generator is used with `perfect = False`, which may leave isolated
pockets in the grid. Collectibles are therefore placed only on the
largest connected component containing the player spawn, computed with a
flood fill. Without this, a level could become impossible to finish —
the worst possible bug to discover during a defense.

### Persistence

Highscores are written to a temporary file then moved into place with an
atomic rename, so a crash or a full disk cannot leave a truncated table
behind. Reading is defensive: a corrupt file yields an empty table plus a
warning, never an exception.
