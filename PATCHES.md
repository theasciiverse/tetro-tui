# Changes from upstream

This is the Asciiverse packaging of [Tetro TUI](https://github.com/Strophox/tetro-tui)
by Strophox (MIT), built from upstream's tag `v3.6.2` (`43f3c95`, 30 July
2026). Upstream is the `upstream` remote; the `asciiverse` branch carries
the changes below. The game itself is unchanged.

## Packaging (new files)

- `.github/workflows/release.yml`: av archives for Linux (static), macOS
  and Windows, each x86-64 and ARM64, plus SHA256SUMS, and .deb, .rpm,
  .apk and Arch packages. Upstream's own `deploy_stuff.yml` runs only on
  plain `vX.Y.Z` tags, so it does not fire for ours.
- `asciiverse/nfpm.yaml`: the system packages.
- `asciiverse/record-preview.py`: records the catalog preview, a Regular
  game played by a driver that reads the screen (it learns each piece's
  rotations by turning it once, then places every piece by height, holes
  and bumpiness).

## Ours

- **How to play it, at the top of README.md.** A short note on installing
  and starting it with av; the original text follows unchanged.
