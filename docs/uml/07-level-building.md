# Building a level

*Activity diagram*

`maze.build_level()` turns a generator maze of *w × h* cells into a playable grid of *(2w+1) × (2h+1)* tiles. Level 1 uses the configured seed; later levels draw a random one.

```mermaid
flowchart TD
  s([Game._generate index]) --> seed{index == 0?}
  seed -- yes --> fixed[seed = config.seed]
  seed -- no --> rand[seed = random 1..2^31-1]
  fixed --> imp
  rand --> imp
  imp[_generator_class: import mazegenerator.MazeGenerator] --> inst[_instantiate: try known constructor signatures, silence stdout]
  inst --> grid[_read_grid: wall bitmasks N=1 E=2 S=4 W=8]
  grid --> tiles[_to_tiles: each cell becomes 2x2 block, walls become WALL tiles]
  tiles --> comp[_largest_component: keep only reachable corridors]
  comp --> pop[_populate: player spawn at centre, 4 ghost spawns near corners, 4 super-pacgums, pacgums clamped to free tiles]
  pop --> lvl([frozen Level])
  imp -. missing package .-> err([MazeError])
  inst -. no signature fits .-> err
```

[Back to the index](README.md)
