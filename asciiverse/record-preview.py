#!/usr/bin/env python3
"""Records asciiverse/tetro-tui.cast, the catalog preview, at 100x30
(hub/RECORDING.md): a Regular game played by a driver that reads the
screen. The first time it meets a piece it turns it all the way round
once, reading each rotation off the screen, so it needs no copy of the
game's rotation system. For every piece it then tries each rotation and
column, scores the resulting well (height, holes, bumpiness, lines
cleared) and sends the keys for the best: rotations, sideways moves, then
a hard drop. After about 50 seconds it quits with Ctrl+C.

The game runs with a throwaway HOME, so nothing touches your own
settings, scores or replays, and is named by bare command, so the cast's
header holds no local path.

Needs asciinema 3.x and pyte. Usage, from the repo root, with the binary
on PATH or in target-musl/release:
  uv run --with pyte python3 asciiverse/record-preview.py
Any extra argument is used as the cast's path instead (for test runs);
DEBUG=1 prints each placement, planned against what locked.
Run it under a memory cap: systemd-run --user --scope -p MemoryMax=4G ..."""
import fcntl, os, pty, select, struct, sys, tempfile, termios, time
import pyte

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cast = sys.argv[1] if len(sys.argv) > 1 else f"{root}/asciiverse/tetro-tui.cast"
COLS, ROWS, PLAY = 100, 30, 50.0
W, H = 10, 20
LEFT, RIGHT, HARD, SOFT = b"\x1b[D", b"\x1b[C", b"\x1b[A", b"\x1b[B"
ROT = b"d"

home = tempfile.mkdtemp(prefix="tetro-preview-")
env = dict(os.environ, TERM="xterm-256color", COLORTERM="truecolor", LANG="C.UTF-8",
           HOME=home, XDG_CONFIG_HOME=f"{home}/.config", XDG_DATA_HOME=f"{home}/.local/share",
           PATH=f"{root}/target-musl/release:{os.environ['PATH']}")
for v in ("VTE_VERSION", "TERM_PROGRAM", "TERM_PROGRAM_VERSION", "TMUX", "KITTY_WINDOW_ID"):
    env.pop(v, None)

pid, fd = pty.fork()
if pid == 0:
    os.chdir(home)
    os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
        "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
        "--title", "tetro-tui", "--command", "tetro-tui", cast], env)
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
screen = pyte.Screen(COLS, ROWS)
stream = pyte.ByteStream(screen)


def pump(seconds):
    end = time.time() + seconds
    while True:
        left = end - time.time()
        r, _, _ = select.select([fd], [], [], max(0.0, min(0.02, left)))
        if r:
            try:
                stream.feed(os.read(fd, 65536))
            except OSError:
                return False
        if left <= 0:
            return True


def key(k, wait=0.07):
    os.write(fd, k)
    pump(wait)


def origin():
    """Screen column and row of the well's top left cell, from its top
    left corner."""
    for y, line in enumerate(screen.display):
        x = line.find("╓")
        if x >= 0:
            return x + 1, y + 1
    return None


def read():
    """(falling, locked): the falling piece's cells and the locked cells,
    as (x, y) in the well, y from 0 at the top; the falling piece may
    stand on the border row above the well (y = -1)."""
    o = origin()
    if not o:
        return set(), set()
    falling, locked = set(), set()
    for y in range(-1, H):
        row = screen.buffer[o[1] + y]
        for x in range(W):
            ch = row[o[0] + 2 * x].data
            if ch == "▓":
                falling.add((x, y))
            elif y >= 0 and ch == "█":
                # locked tiles; line clear and lock effects draw other
                # glyphs for a moment, which must not count
                locked.add((x, y))
    return falling, locked


def norm(cells):
    mx = min(x for x, _ in cells)
    my = min(y for _, y in cells)
    return frozenset((x - mx, y - my) for x, y in cells)


def drop(locked, shape, col):
    """Cells where shape lands with its left edge at col, or None."""
    if any(not 0 <= col + dx < W for dx, _ in shape):
        return None
    y = -3
    while all((col + dx, y + 1 + dy) not in locked and y + 1 + dy < H for dx, dy in shape):
        y += 1
    cells = {(col + dx, y + dy) for dx, dy in shape}
    return None if any(cy < 0 for _, cy in cells) else cells


def evaluate(cells):
    full = [y for y in range(H) if all((x, y) in cells for x in range(W))]
    if full:
        cells = {(x, y + sum(1 for f in full if f > y)) for x, y in cells if y not in full}
    heights, holes = [], 0
    for x in range(W):
        col = [y for (cx, y) in cells if cx == x]
        top = min(col) if col else H
        heights.append(H - top)
        holes += sum(1 for y in range(top, H) if (x, y) not in cells)
    bump = sum(abs(heights[i] - heights[i + 1]) for i in range(W - 1))
    return -0.51 * sum(heights) + 0.76 * len(full) - 0.36 * holes - 0.18 * bump


def wait_piece(previous, timeout=3.0):
    """Waits for a new falling piece near the top, and the well to settle."""
    end = time.time() + timeout
    while time.time() < end:
        pump(0.05)
        falling, locked = read()
        if len(falling) == 4 and min(y for _, y in falling) <= 1:
            pump(0.1)
            again = read()
            if again[1] == locked and len(again[0]) == 4:
                return again
    return read()


shapes = {}          # norm(rotation 0) -> four normalised rotations


def learn(falling):
    rots = [norm(falling)]
    for _ in range(3):
        key(ROT, 0.12)
        f, _ = read()
        rots.append(norm(f) if len(f) == 4 else rots[-1])
    key(ROT, 0.12)
    return rots


# title menu: New Game, then Regular
pump(2.5)
key(b"\r", 0.8)
key(b"\r", 1.2)

start = time.time()
previous = set()
pieces = 0
while time.time() - start < PLAY:
    falling, locked = wait_piece(previous)
    if len(falling) != 4:
        break
    # bring the piece fully into the well first: at the ceiling some
    # turns are blocked, and an upright I would reach above the border row
    for _ in range(2):
        key(SOFT, 0.06)
    falling, locked = read()
    if len(falling) != 4:
        break
    k = norm(falling)
    if k not in shapes:
        shapes[k] = learn(falling)
        falling, locked = read()
    best, choice = None, None
    for r, shape in enumerate(shapes[k]):
        for col in range(W):
            cells = drop(locked, shape, col)
            if cells is None:
                continue
            s = evaluate(locked | cells)
            if best is None or s > best:
                best, choice = s, (r, col)
    if choice is None:
        break
    r, col = choice
    planned = drop(locked, shapes[k][r], col)
    for _ in range(r):
        key(ROT, 0.06)
    f, _ = read()
    if len(f) == 4:
        dx = col - min(x for x, _ in f)
        for _ in range(abs(dx)):
            key(RIGHT if dx > 0 else LEFT, 0.05)
    pump(0.12)
    key(HARD, 0.45)  # the drop trail, lock and line clear effects pass first
    if os.environ.get("DEBUG"):
        _, after = read()
        new = after - locked
        print(f"piece {pieces} r={r} col={col} planned={sorted(planned)} got={sorted(new)} learned={[sorted(x) for x in shapes[k]]}", file=sys.stderr)
    previous = falling
    pieces += 1

pump(1.5)
key(b"\x03", 0.5)
for _ in range(50):
    if os.waitpid(pid, os.WNOHANG)[0]:
        break
    time.sleep(0.2)
print(f"{pieces} pieces", file=sys.stderr)
