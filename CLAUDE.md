# Tetro TUI (Asciiverse packaging)

Strophox's tetromino-stacking game in Rust (crossterm and the
falling-tetromino-engine crate); packaged for the Asciiverse catalog and
as system packages. Not our code: keep changes small, list every one in
PATCHES.md, and offer fixes upstream. Never call it Tetris in store text.

- Remotes: `upstream` is github.com/Strophox/tetro-tui, `origin` is
  github.com/theasciiverse/tetro-tui.
- Branch `asciiverse` = an upstream release tag plus our commits; tag
  `v<version>-av.<n>` and push it.
- Local static build: `docker run --rm --memory=4g -v "$PWD":/src -w /src
  rust:1-alpine cargo build --release --locked --target-dir target-musl`.
- Run tests and recordings under `systemd-run --user --scope -p
  MemoryMax=4G`.
- The save file is `~/.config/.tetro-tui_v3.6_savefile.ron` (a hidden file
  straight in the config folder, named for the major and minor version).
- Keys in a plain terminal: arrows move, `a`/`d` rotate, Up hard drop,
  Down soft drop, Esc pause, Ctrl+C quits at once.
- On screen the falling piece is `▓▓`, its shadow `░░`, locked tiles
  `██`; a piece can spawn partly on the well's top border row, and the
  S and Z cannot turn there.
