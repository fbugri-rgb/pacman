# One frame while playing

*Sequence diagram*

`App.run()` repeats this at 60 FPS. Delta time is clamped to 50 ms so a stalled window never teleports Pac-Man through walls.

```mermaid
sequenceDiagram
  participant A as App
  participant D as Display
  participant G as Game
  participant P as Player
  participant Gh as Ghost x4
  participant UI as ui

  A->>D: tick()
  D-->>A: delta (≤ 0.05 s)
  A->>D: poll()
  D-->>A: KeyPress list, closed?
  loop each key press
    A->>A: _handlers[screen](press)
    opt arrow or WASD
      A->>G: steer(direction)
    end
  end
  A->>G: update(delta)
  G->>G: _tick_timers (time limit, frightened, scatter/chase)
  G->>P: update(delta, level, picker)
  G->>G: _collect() pacgums, super-pacgums
  opt not frozen by cheat
    G->>Gh: update(delta, level, picker)
  end
  G->>G: _resolve_contacts() eat ghost or lose life
  G-->>A: status
  alt LEVEL_CLEARED
    A->>A: screen = LEVEL_CLEARED
  else GAME_OVER or VICTORY
    A->>A: _finish(won)
  end
  A->>UI: draw_game(display, game, elapsed)
  UI->>D: rect / disc / text
  A->>D: present()
```

[Back to the index](README.md)
