# 🟩 contribution_writer

Write words into your GitHub contribution graph by creating backdated commits
that form letter shapes — one word per year.

```

python contribution_writer.py "MY SENTENCE" 2022 /path/to/repo

```

---

## How It Works

The GitHub contribution graph is a **7-row × 52-column** matrix:

- **X axis** — weeks of the year (columns 0–51)
- **Y axis** — days of the week (row 0 = Sunday … row 6 = Saturday)

Each year starts at the **first Sunday on or before January 1st**.

The script renders each word using a built-in **5×7 pixel font**, maps every
lit pixel to a calendar date, and creates backdated git commits on those dates.
GitHub reads the `GIT_AUTHOR_DATE` of each commit to place the green square
in the right cell of the graph.

---

## Requirements

- Python **3.10+**
- `git` installed and available in `PATH`
- A git repository that already has **at least one commit** on `main`
- The repo's `git config user.email` must match your **GitHub account email**

---

## Installation

No dependencies beyond the Python standard library. Just clone or download the script:

```bash
curl -O https://raw.githubusercontent.com/your-username/your-repo/main/contribution_writer.py
```

---

## Usage

```
python contribution_writer.py [OPTIONS] SENTENCE START_YEAR REPO_PATH
```

### Arguments

| Argument     | Description                                         |
| :----------- | :-------------------------------------------------- |
| `SENTENCE`   | The sentence to write. Each word occupies one year. |
| `START_YEAR` | The first year to write into (e.g. `2022`).         |
| `REPO_PATH`  | Path to the local git repository.                   |

### Options

| Flag                          | Default | Description                                   |
| :---------------------------- | :------ | :-------------------------------------------- |
| `-c`, `--commits-per-pixel N` | `3`     | Commits per lit pixel. Higher = darker green. |
| `-n`, `--dry-run`             | `false` | Preview bitmaps only — no commits created.    |
| `-h`, `--help`                |         | Show help message and exit.                   |

---

## Examples

```bash
# 1. Preview without touching the repo (always do this first!)
python contribution_writer.py --dry-run "HELLO WORLD" 2022 .

# 2. Write for real with default intensity (medium green)
python contribution_writer.py "HELLO WORLD" 2022 /path/to/repo

# 3. Darker squares — 6 commits per pixel
python contribution_writer.py "HELLO WORLD" 2022 /path/to/repo -c 6

# 4. Push to GitHub when done
cd /path/to/repo && git push origin main
```

### Dry-run preview output

```
📅  Year 2022  →  'HELLO'
  ┌────────────────────────────────────────────────────┐
  │           █   █ █████ █     █      ███             │
  │           █   █ █     █     █     █   █            │
  │           █   █ █     █     █     █   █            │
  │           █████ ████  █     █     █   █            │
  │           █   █ █     █     █     █   █            │
  │           █   █ █     █     █     █   █            │
  │           █   █ █████ █████ █████  ███             │
  └────────────────────────────────────────────────────┘
  (73 active pixels)
```

---

## Green Intensity Guide

| `--commits-per-pixel` | Square colour        |
| :-------------------- | :------------------- |
| 1                     | 🟩 Lightest green    |
| 3 _(default)_         | 🟩🟩 Medium green    |
| 6+                    | 🟩🟩🟩 Darkest green |

---

## Supported Characters

```
A–Z   0–9   ! ? . , - ' # (space)
```

All input is automatically uppercased.

---

## Tips \& Gotchas

- **Always dry-run first** — use `-n` to check the layout before creating commits.
- **Long words get clipped** — a 5-wide font with 1-column gaps fits ~8 characters
  comfortably in 52 columns. Use abbreviations for longer words.
- **Private contributions** — if the repo is private, enable _"Private contributions"_
  in your GitHub profile settings, otherwise the squares won't show.
- **Dedicated repo** — use a throwaway repo (e.g. `github-art`) to avoid polluting
  a real project's history.
- **Don't force-push real work** — backdated commits are appended to history; this
  is safe on a fresh repo but may require `--force` if the remote has diverged.
- **Year boundary pixels** — the first column of a year's graph can start in
  December of the previous year. The script handles this correctly.

---

## How to Set Up a Dedicated Repo

```bash
# 1. Create a new repo on GitHub (e.g. "github-art"), then:
mkdir github-art && cd github-art
git init
git commit --allow-empty -m "init"
git remote add origin git@github.com:your-username/github-art.git
git push -u origin main

# 2. Run the script
python contribution_writer.py "HELLO WORLD" 2024 ./github-art

# 3. Push
cd github-art && git push origin main
```

---

## License

MIT — do whatever you want, but maybe don't spam `git push --force` on your
employer's main branch.
