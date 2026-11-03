# Module dependencies

*Package diagram*

The entry script only knows `app`, `config` and `render`. Pygame is touched in one place, `render.py`, and the A-Maze-ing wheel is imported lazily by `maze.py`. `constants.py` sits at the bottom and depends on nothing.

```mermaid
flowchart TB
  entry["pac-man.py<br/>main(argv)"]
  subgraph pkg["package pacman"]
    app["app.py<br/>App, run_game"]
    ui["ui.py<br/>draw_* functions"]
    game["game.py<br/>Game, Cheats"]
    entities["entities.py<br/>Actor, Player, Ghost"]
    maze["maze.py<br/>Level, build_level"]
    config["config.py<br/>GameConfig, load_config"]
    hs["highscores.py<br/>HighscoreTable"]
    render["render.py<br/>Display, KeyPress"]
    constants["constants.py<br/>enums, colors, sizes"]
  end
  pygame[("pygame")]
  mg[("mazegenerator<br/>A-Maze-ing wheel")]
  cfg[/"config.json"/]
  hsf[/"highscores.json"/]

  entry --> app
  entry --> config
  entry --> render
  app --> ui
  app --> game
  app --> hs
  app --> render
  app --> config
  ui --> game
  ui --> entities
  ui --> maze
  ui --> render
  ui --> hs
  game --> entities
  game --> maze
  game --> config
  entities --> maze
  render --> pygame
  maze -. "importlib" .-> mg
  config -. reads .-> cfg
  hs -. "reads / writes" .-> hsf
  app --> constants
  ui --> constants
  entities --> constants
  maze --> constants
  render --> constants
```

[Back to the index](README.md)
