# Startup

*Sequence diagram*

From `python3 pac-man.py config.json` to the first frame. A frozen build with no argument falls back to the `config.json` bundled by PyInstaller.

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Main as pac-man.py
  participant Cfg as config.py
  participant RG as app.run_game
  participant D as Display
  participant A as App
  participant HS as HighscoreTable

  User->>Main: python3 pac-man.py config.json
  alt no argument
    Main->>Main: bundled_config() via sys._MEIPASS
  end
  alt argument count is not 1
    Main-->>User: usage on stderr, exit 1
  end
  Main->>Cfg: load_config(path)
  Cfg->>Cfg: strip_json_comments, json.loads
  Cfg->>Cfg: parse_config: clamp values, pad to 10 levels
  alt unreadable or invalid JSON
    Cfg-->>Main: ConfigError
    Main-->>User: error on stderr, exit 1
  end
  Cfg-->>Main: GameConfig (with warnings)
  Main->>Main: report_warnings(config)
  Main->>RG: run_game(config)
  RG->>D: Display(1000, 760, TITLE)
  alt no video device
    D-->>Main: DisplayError, exit 1
  end
  RG->>A: App(config, display)
  A->>HS: HighscoreTable(path).load()
  RG->>A: run()
  Note over A: frame loop until Screen.QUIT
  RG->>D: close()
  Main-->>User: exit 0
```

[Back to the index](README.md)
