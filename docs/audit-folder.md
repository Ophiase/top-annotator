# The audit folder

`top-annotator paths` lists every place the tool reads or writes, and which
ones your user can write.

## Two layers

The tool reads two layers, wherever it is launched from:

| Layer | Where | Who writes it |
| --- | --- | --- |
| Base audit | `src/top_annotator/audit/base/`, bundled | a commit to this repository |
| Your annotations | `~/.local/share/top-annotator/session.yaml` | the TUI and `annotate` |

- Your layer wins; clearing an entry falls back to the base.
- `--cache PATH` or `$TOP_ANNOTATOR_AUDIT` replaces the base.
- `$TOP_ANNOTATOR_DATA_DIR` moves your layer; `$XDG_DATA_HOME` is honoured.
- The app never writes the base. The status line and `--help` show both.

## The base: scope, then family

The base is split first by **distribution scope**, then by family, then into
files of about 20 entries:

```text
base/
  common/          true on any distribution
  <id>/            one folder per /etc/os-release id
    system/        boot, network, hardware, services
    <desktop>/     the desktop's session and settings
    programs/      third-party programs
```

- A machine reads `common/` plus the folders its `ID` and `ID_LIKE` name: a
  derivative reads its own folder and its base's.
- An Arch machine reads `common` and `arch`, never an Ubuntu entry.
- A folder without `common/`, such as one given with `--cache`, is read whole.
- The status line shows which folders were read.

Which distributions are covered, and how to add one, is in
[CONTRIBUTING.md](../CONTRIBUTING.md#auditing-a-distribution).

## Suggestions

A `suggestions/` folder inside a family holds entries for **optional**
programs: a GPU driver, a VPN, Docker, an applet some people install.

- A suggestion is never trusted: the process stays `NEW`, with a `sug` hint.
- `Enter` shows the suggested level and note; `A` copies it into your layer,
  as your decision, journaled and undoable like any other change.
- Agents see it as `suggested` in `snapshot`.
- The base proper keeps only what every install of a distribution runs.

## The file shape

```yaml
version: 1
annotations:
  gsd-xsettings|/usr/libexec/gsd-xsettings:
    category: safe
    provider: distro
    note: GNOME Settings Daemon module; package gnome-settings-daemon
    updated: 2026-11-01
  bwrap|/usr/bin/bwrap: safe
```

- A missing entry means unannotated.
- A bare category string is accepted for quick hand edits.
- An entry without `provider` loads and shows an empty cell.

## History and undo

Every change to your layer is appended to `history.jsonl`, next to
`session.yaml`: one JSON line per change, with the time, the signature and
the entry before and after.

- It tells when a rule was first set and last changed (details screen, `R`).
- `u` or `top-annotator undo` puts back what the latest change replaced.
- An undo is a new line naming what it reverts: nothing is ever rewritten.

The journal is a plain file: see [hardening.md](hardening.md) for what that
does and does not protect.

## Treat it as a fingerprint

An audit names the packages, paths and services installed on a machine. Share
a base made of what every install of a distribution runs; keep what only your
machine runs in your own layer.
