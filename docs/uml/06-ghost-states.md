# Ghost lifecycle

*State diagram*

Each ghost carries a `GhostState`. While chasing, the whole pack alternates between a 7 s scatter phase (head for the home corner) and a 20 s chase phase.

```mermaid
stateDiagram-v2
  [*] --> CHASE
  state CHASE {
    [*] --> Scatter
    Scatter --> Hunt : after 7 s
    Hunt --> Scatter : after 20 s
  }
  CHASE --> FRIGHTENED : player eats super-pacgum
  FRIGHTENED --> CHASE : super_pacgum_duration ends
  FRIGHTENED --> EATEN : touched by player
  EATEN --> CHASE : respawn_timer reaches 0, back in home corner
  CHASE --> CHASE : touches player, life lost
```

[Back to the index](README.md)
