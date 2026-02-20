#!/usr/bin/env python3
"""
contribution_writer.py
======================
"Writes" each word of a sentence into the GitHub contribution graph
by creating backdated git commits that form letter shapes.

Graph layout (GitHub default):
  - X axis: weeks (columns 0–51)
  - Y axis: days of week, row 0 = Sunday (top), row 6 = Saturday (bottom)
  - Each year starts at the first Sunday on or before Jan 1

Usage
-----
  # Dry-run preview (no commits):
  python contribution_writer.py --dry-run "MY SENTENCE" 2022 /path/to/repo

  # Write for real (3 commits per active pixel → medium green):
  python contribution_writer.py "MY SENTENCE" 2022 /path/to/repo

  # Darker green (more commits per pixel):
  python contribution_writer.py "MY SENTENCE" 2022 /path/to/repo --commits-per-pixel 6

After running, push with:
  cd /path/to/repo && git push origin main

Requirements
------------
  - Python 3.10+
  - git installed and in PATH
  - The repo must already be initialised (`git init` + at least one commit)
  - The git user.email in the repo must match your GitHub account email
"""

import argparse
import os
import subprocess
import sys
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# 5×7 pixel bitmap font
# Row 0 = top of glyph, Row 6 = bottom
# Each string is 5 chars wide ('0' = off, '1' = on)
# ---------------------------------------------------------------------------
FONT: dict[str, list[str]] = {
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11100", "10010", "10001", "10001", "10001", "10010", "11100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10001", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "01010", "01010", "00100", "01010", "01010", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "00000", "00100"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00100", "01000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "'": ["00100", "00100", "00000", "00000", "00000", "00000", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
}

GRAPH_ROWS = 7  # rows  → days of week  (0=Sun … 6=Sat)
GRAPH_COLS = 52  # cols  → weeks of year


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_year_start(year: int) -> date:
    """Return the first Sunday on or before Jan 1 of *year*.

    GitHub's contribution graph for a given year starts on this date,
    which can be in December of the previous year.
    """
    jan1 = date(year, 1, 1)
    # isoweekday: Mon=1 … Sun=7  →  days since last Sunday = isoweekday % 7
    days_since_sunday = jan1.isoweekday() % 7  # Sun→0, Mon→1, …, Sat→6
    return jan1 - timedelta(days=days_since_sunday)


def render_word(word: str, center: bool = True) -> list[list[int]]:
    """Render *word* into a 7×52 bitmap centred on the contribution graph.

    Returns a list of GRAPH_ROWS rows, each a list of GRAPH_COLS ints (0/1).
    Unknown characters are silently replaced with a space.
    """
    word = word.upper()
    columns: list[list[int]] = [[] for _ in range(GRAPH_ROWS)]

    for idx, ch in enumerate(word):
        glyph = FONT.get(ch, FONT[" "])
        if idx > 0:  # 1-column gap between letters
            for r in range(GRAPH_ROWS):
                columns[r].append(0)
        for r in range(GRAPH_ROWS):
            columns[r].extend(int(b) for b in glyph[r])

    text_width = len(columns[0])
    bitmap = [[0] * GRAPH_COLS for _ in range(GRAPH_ROWS)]
    offset = max(0, (GRAPH_COLS - text_width) // 2) if center else 1

    for r in range(GRAPH_ROWS):
        for c, val in enumerate(columns[r]):
            dest = offset + c
            if 0 <= dest < GRAPH_COLS:
                bitmap[r][dest] = val

    return bitmap


def bitmap_to_dates(bitmap: list[list[int]], year: int) -> list[date]:
    """Convert a 7×52 bitmap to a sorted list of dates for every lit pixel."""
    origin = get_year_start(year)
    dates: list[date] = []
    for col in range(GRAPH_COLS):
        for row in range(GRAPH_ROWS):
            if bitmap[row][col]:
                dates.append(origin + timedelta(weeks=col, days=row))
    return sorted(dates)


def print_bitmap(word: str, bitmap: list[list[int]]) -> None:
    """Pretty-print the bitmap to stdout."""
    bar = "─" * GRAPH_COLS
    print(f"  ┌{bar}┐")
    for row in bitmap:
        print(f"  │{''.join('█' if p else ' ' for p in row)}│")
    print(f"  └{bar}┘")
    lit = sum(sum(r) for r in bitmap)
    fits = len(word) <= (GRAPH_COLS // 6)
    if not fits:
        print(
            f"  ⚠️  '{word}' is long ({len(word)} chars) — some letters may be clipped!"
        )
    else:
        print(f"  ({lit} active pixels)")


# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: str, env: dict | None = None) -> None:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        print(f"  ⚠️  git error: {result.stderr.decode().strip()}", file=sys.stderr)
        result.check_returncode()


def make_commit(repo: str, on_date: date, env: dict) -> None:
    """Append one line to a marker file and create a single backdated commit."""
    marker = os.path.join(repo, ".graph_art")
    with open(marker, "a") as fh:
        fh.write(f"{on_date.isoformat()}\n")
    _run(["git", "add", ".graph_art"], cwd=repo)
    _run(
        ["git", "commit", "-m", f"graph: pixel {on_date.isoformat()}"],
        cwd=repo,
        env=env,
    )


def write_word(
    word: str,
    year: int,
    repo: str,
    commits_per_pixel: int,
    dry_run: bool,
) -> None:
    bitmap = render_word(word)
    print_bitmap(word, bitmap)

    if dry_run:
        return

    dates = bitmap_to_dates(bitmap, year)
    total = len(dates) * commits_per_pixel
    print(f"  → {len(dates)} pixels × {commits_per_pixel} commits = {total} commits …")

    base_env = os.environ.copy()
    for i, d in enumerate(dates, 1):
        ts = d.strftime("%Y-%m-%dT12:00:00 +0000")
        env = {**base_env, "GIT_AUTHOR_DATE": ts, "GIT_COMMITTER_DATE": ts}
        for _ in range(commits_per_pixel):
            make_commit(repo, d, env)
        if i % 10 == 0 or i == len(dates):
            print(f"  ├─ {i}/{len(dates)} pixels done …", end="\r")

    print(f"  ✅  {year} — '{word}' written ({total} commits created).{' ' * 20}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="contribution_writer.py",
        description="Write words in the GitHub contribution graph via backdated commits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Preview without making any commits:
  python contribution_writer.py --dry-run "YOLO PUSHED" 2023 .

  # Actually write the commits (medium green intensity):
  python contribution_writer.py "YOLO PUSHED" 2023 /path/to/repo

  # Darker squares (more commits per pixel):
  python contribution_writer.py "YOLO PUSHED" 2023 /path/to/repo -c 6

notes:
  • One word is written per year, starting from start_year.
  • The git user.email in the repo must match your GitHub account email.
  • Commit counts per intensity level (approximate):
      1 commit  → lightest green
      3 commits → medium green   (default)
      6+ commits → darkest green
  • After running, push to GitHub:
      cd /path/to/repo && git push origin main
        """,
    )
    parser.add_argument(
        "sentence", help="Sentence to write (one word per year, space-separated)"
    )
    parser.add_argument("start_year", type=int, help="First year to start writing from")
    parser.add_argument("repo_path", help="Path to the local git repository")
    parser.add_argument(
        "--commits-per-pixel",
        "-c",
        type=int,
        default=3,
        metavar="N",
        help="Commits per lit pixel — higher = darker green square (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview bitmaps only, do not create any commits",
    )
    args = parser.parse_args()

    repo = os.path.abspath(args.repo_path)

    if not args.dry_run:
        if not os.path.isdir(os.path.join(repo, ".git")):
            sys.exit(f"❌  '{repo}' is not a git repository (no .git folder found).")
        if args.commits_per_pixel < 1:
            sys.exit("❌  --commits-per-pixel must be at least 1.")

    words = args.sentence.split()
    if not words:
        sys.exit("❌  Empty sentence.")

    mode = (
        "DRY RUN — preview only"
        if args.dry_run
        else f"{args.commits_per_pixel} commit(s)/pixel"
    )
    print(f"\n✍️   GitHub Contribution Graph Writer")
    print(f"     Sentence : {args.sentence}")
    print(f"     Years    : {args.start_year} – {args.start_year + len(words) - 1}")
    print(f"     Mode     : {mode}\n")

    for i, word in enumerate(words):
        year = args.start_year + i
        print(f"📅  Year {year}  →  '{word}'")
        write_word(word, year, repo, args.commits_per_pixel, args.dry_run)
        print()

    if not args.dry_run:
        print("🎉  All done! Push to GitHub with:")
        print(f"    cd {repo} && git push origin main")
    else:
        print("✅  Dry run complete. Re-run without --dry-run to create commits.")


if __name__ == "__main__":
    main()
