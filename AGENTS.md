# AGENTS.md

Instructions for any coding agent working in this repository. Claude Code
reads this file through `.claude/CLAUDE.md`; other agents read it directly.

## What this project is

A small interactive terminal process viewer. It reads `/proc`, draws the
process tree, and lets the developer annotate what they have audited. Its
single purpose is to make the **not yet audited** processes obvious.

Stack: Python 3.14, uv, just, Ruff, Ty, Textual, PyYAML.

- [README.md](README.md) — the pitch and install; [docs/](docs/) — the
  screen, signatures, trust, the audit folder, agents and hardening
- [.agents/](.agents/) — project policy, the Kanon and the portable rules
- [.agents/portable/](.agents/portable/) — the portable layer; it stays
  project-agnostic and is guarded by `portable.sh`
- [.agents/checks/](.agents/checks/) — project checks and the check runner
- [.agents/kanon.md](.agents/kanon.md) — the canon; `<>` is its sign
- [.agents/skills/audit/](.agents/skills/audit/SKILL.md) — the `audit`
  skill: `analyse` (read-only, a post-it report) and `update` (classify the
  unannotated)

## Language

English everywhere: code, comments, identifiers, markdown, commits. The user
may write French; answer in French, write files in English.

## Read before working

- [.agents/portable/rules/python.md](.agents/portable/rules/python.md) — the
  portable Python rules
- [.agents/portable/rules/comments.md](.agents/portable/rules/comments.md) —
  when a comment earns its place
- [.agents/portable/rules/urls.md](.agents/portable/rules/urls.md) — a URL in
  code is justified on its line
- [.agents/rules/python.md](.agents/rules/python.md) — what portable leaves to
  this repository
- [.agents/rules/tui.md](.agents/rules/tui.md) — before touching a binding, a
  screen or the table

Open the matching guide yourself; do not assume another agent loaded it.

## Toolchain

- `uv sync` installs; `uv run top-annotator` runs; `uv run pytest` tests.
- `just` wraps the usual commands. `just checks` is markdown lint + lint +
  format check + `ty check` + tests, one command and a real exit code.
- `just guards` runs the portable and project checks over the changed files.
  `just gate` is `checks` then `guards`: the one command to declare work done.
- Never `pip install` into the environment and never create a venv by hand.
- Python 3.14 syntax is allowed, including unparenthesized multi-exception
  `except OSError, ValueError:` as Ruff formats it.

## Layout

`src/top_annotator/`, imported as `top_annotator`:

- `__main__.py` — argparse, TUI and agent subcommands
- `agent.py` — JSON snapshot/rules/annotate/verify payloads
- `audit/` — store, YAML I/O, journal, family routing; `review/` holds rule
  rows and suggestions
- `core/` — category, annotation, process info, sections, tree
- `process/` — scan, signature, heuristics, cache, verification;
  `scan/demo/` is the fictional machine behind `--demo`
- `tui/` — app, actions mixins, screens, table, theme, palette

Each folder holds at most seven entries. Each module holds one class. Every
Python file stays under 200 code lines; `file-length`, `one-class`,
`folder-size`, `no-protocol` and the other portable checks enforce it.

Tests are grouped in `tests/{agent,audit,core,process,tui}/`;
`factories.process()` makes a `ProcessInfo`.

## Invariants

- **Read-only process access.** Never send a signal, never terminate, never
  write to another process. The tool exists to observe and annotate.
- **No network.** No telemetry, update check, font or remote asset.
- **The audit YAML is user data.** Preserve notes when changing category, write
  atomically, and keep hand-written category strings loading.
- **Signatures are stable.** Name + resolved executable, plus the script for
  known interpreters. Changing the format breaks every existing annotation;
  treat it as a migration.
- **`sys?` is a hint, never an automatic annotation.** The human decides what
  is safe. A base `suggestions/` entry is the same: shown as `sug`, accepted
  only by `A` into the user's layer, never trusted on load.
- **Search keeps context.** A matching process always appears with its full
  ancestor chain; a flat PID dump is not acceptable.
- **Kernel threads are background.** The `kernel` group is folded and last by
  default, its threads split by name family, each folded; a user fold/unfold
  wins and is not reset by a refresh. A family name explains, never vouches.
- **A fold is local to its band.** A fold key names the band or provider group
  it was made in plus the PID; folding a process under `NEW` never folds it
  under `SAFE`. The `SAFE` provider groups are sorted riskiest first;
  `unlabelled`, `app`, `service` and `desktop` start open, the system groups
  folded.
- **Unannotated must win the eye.** The default view is `WEIRD`, `NEW`, then
  `SAFE`; `NEW` is bold red; the `sys?` hint is secondary; annotated rows use
  their category color.
- **Trust is graduated.** `s` is the fast `trust` mark; `S` opens the precise
  picker (`core`, `safe`, `audited`, `trust`, `personal`, `watch`, `unsafe`,
  and `unreviewed` to remove the annotation).
  Never make `s` mean `safe` again.
- **A parent vouches only for its direct children.** `children` covers the
  names it lists, one level down; `exclusive` turns every other child `WEIRD`.
  Never let coverage reach grandchildren. A `terminal` covers its shells; an
  `interactive` program is trusted only when typed in one of them; an `agent`
  covers its shells the same way.
- **`WEIRD` is a prompt, not a verdict.** A masquerade pattern or an explicit
  `watch` / `unsafe` annotation lands there; the human still decides.
- **Provider is not trust.** `provider` says what a process is or who ships it
  (`app`, `service`, `desktop`, `derivative`, `distro`, `systemd`, `kernel`);
  the TUI names `distro` and `derivative` from `/etc/os-release`. The trust
  level says how much it is trusted. Never derive one from the other.
- **Families do not mix, nor distributions.** Each scope (`common/`,
  `ubuntu/`, `pop/`) and each family under it holds its own entries; an
  existing annotation is never moved by a category change.

## Audit folder and session

Two layers, independent of the working directory. The base audit is bundled
with the tool in `src/top_annotator/audit/base/`, split first by
distribution scope (`common/`, `ubuntu/`, `pop/`; a machine reads `common/`
plus the ids its `/etc/os-release` names), then by family (`system/`,
`gnome/`, `cosmic/`, `programs/`), then into small files. Keep each file under
roughly 20 entries; never put one distribution's entry in another's folder.
It is tracked on purpose so two people can share an audit; `--cache` or
`$TOP_ANNOTATOR_AUDIT` replaces it.

The user's layer is `$XDG_DATA_HOME/top-annotator/session.yaml`
(`$TOP_ANNOTATOR_DATA_DIR` moves it). It is user data, never a cache. Every
change to it is appended to `history.jsonl` beside it; the journal is
append-only, and undo is a new line, never a rewrite. The app
never writes the base: TUI and `annotate` write the user's layer, which
overrides the base at load time; clearing it falls back to the base entry.

An agent asked to record a review either edits the base (a versioned change,
shared with the project) or runs `annotate` (local to this user), as asked.
