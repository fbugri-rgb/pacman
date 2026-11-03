# Core types

*Class diagram*

`App` owns the window, the highscore table and at most one `Game`. A `Game` owns the current `Level`, one `Player` and four `Ghost`s. Configuration and levels are frozen dataclasses that flow down, never up.

```mermaid
classDiagram
  direction TB
  class App {
    +GameConfig config
    +Screen screen
    +Game game
    -Display _display
    -HighscoreTable _table
    -dict _handlers
    +run()
    -_update(delta)
    -_draw()
    -_start_game()
    -_finish(won)
  }
  class Display {
    +tick() float
    +poll() list~KeyPress~, bool
    +clear(color)
    +rect(...)
    +disc(...)
    +text(...)
    +present()
    +close()
  }
  class KeyPress {
    <<dataclass>>
    +str name
    +str char
  }
  class HighscoreTable {
    +entries list~Entry~
    +load()
    +qualifies(score) bool
    +add(name, score)
    +save() bool
  }
  class Entry {
    <<dataclass>>
    +str name
    +int score
  }
  class GameConfig {
    <<frozen dataclass>>
    +str highscore_filename
    +tuple~LevelConfig~ levels
    +int lives
    +int seed
    +float player_speed
    +float super_pacgum_duration
    +bool cheats_enabled
    +tuple~str~ warnings
  }
  class LevelConfig {
    <<frozen dataclass>>
    +int width
    +int height
    +int pacgum
    +int max_time
    +float ghost_speed
  }
  class Game {
    +int score
    +int lives
    +int level_index
    +GameStatus status
    +Level level
    +Player player
    +list~Ghost~ ghosts
    +float time_left
    +float frightened_timer
    +bool scatter
    +update(delta)
    +steer(direction)
    +next_level() bool
  }
  class Cheats {
    <<dataclass>>
    +bool invincible
    +bool frozen
    +bool fast
    +bool used
  }
  class Level {
    <<frozen dataclass>>
    +tiles
    +Position player_spawn
    +tuple ghost_spawns
    +frozenset pacgums
    +frozenset super_pacgums
    +int seed
    +is_wall(x, y) bool
  }
  class Actor {
    +Position tile
    +Position next_tile
    +float progress
    +Direction direction
    +float speed
    +update(delta, level, pick) int
    +reset(spawn, direction)
    +reverse()
  }
  class Player {
    +Direction desired
    +bool started
    +steer(direction, level)
    +picker(level)
  }
  class Ghost {
    +int index
    +Position home
    +GhostState state
    +float respawn_timer
    +frighten()
    +eaten(delay)
    +target(...)
    +picker(...)
  }
  class Screen {
    <<enumeration>>
    MENU
    HIGHSCORES
    INSTRUCTIONS
    PLAYING
    PAUSED
    LEVEL_CLEARED
    NAME_ENTRY
    ERROR
    QUIT
  }
  class GameStatus {
    <<enumeration>>
    RUNNING
    LEVEL_CLEARED
    GAME_OVER
    VICTORY
  }

  App o-- Display : draws on
  App *-- HighscoreTable
  App *-- "0..1" Game
  App --> Screen
  App ..> KeyPress : handles
  App --> GameConfig
  HighscoreTable *-- "0..10" Entry
  GameConfig *-- "10..*" LevelConfig
  Game --> GameConfig
  Game *-- Cheats
  Game *-- Level
  Game *-- "1" Player
  Game *-- "4" Ghost
  Game --> GameStatus
  Actor <|-- Player
  Actor <|-- Ghost
  Actor ..> Level : moves on
```

- `Position` is an alias for `tuple[int, int]`, a tile coordinate.
- `Direction`, `Tile` and `GhostState` are enums in `constants.py`.
- Ghost indices 0–3 map to Blinky, Pinky, Inky and Clyde, each with its own `target()` rule.

[Back to the index](README.md)
