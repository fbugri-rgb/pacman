# Build and release

*Deployment diagram*

Local work goes through the `Makefile`. A pushed `v*` tag or a manual run of `release.yml` lints, tests, freezes on three runners and pushes to Itch.io with butler.

```mermaid
flowchart LR
  subgraph dev["Developer machine"]
    mi["make install<br/>requirements.txt + mazegenerator wheel"]
    mr["make run<br/>pac-man.py config.json"]
    ml["make lint<br/>flake8 + mypy"]
    mt["make test<br/>pytest tests/"]
    mp["make package<br/>build.sh"]
    mi --> mr
    mi --> ml
    mi --> mt
    mi --> mp
  end

  subgraph gha["GitHub Actions: release.yml"]
    check["check<br/>ubuntu-22.04<br/>install, lint, test"]
    subgraph matrix["build matrix"]
      bl["ubuntu-22.04<br/>linux"]
      bw["windows-latest<br/>windows"]
      bm["macos-latest<br/>mac (Apple Silicon)"]
    end
    pub["publish<br/>butler push per channel"]
    check --> bl & bw & bm
    bl & bw & bm -- "release-*.tar" --> pub
  end

  subgraph bs["build.sh"]
    b1["check PyInstaller, pygame, mazegenerator"] --> b2["PyInstaller pacman.spec<br/>bundles config.json"] --> b3["stage dist/release<br/>binary + config.json + README"] --> b4["zip pac-man-PLATFORM.zip"]
  end

  tag(["git tag v*<br/>or Run workflow"]) --> check
  matrix -. runs .-> bs
  mp -. runs .-> bs
  pub --> itch[("Itch.io<br/>fbugri-rgb/pacman")]
  secret{{"BUTLER_API_KEY secret"}} -.-> pub
```

[Back to the index](README.md)
