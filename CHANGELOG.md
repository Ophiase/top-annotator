# CHANGELOG

Milestones of the whole project; the version is in `VERSION`.

## Ideas

- daemon-inspector
  - sometimes you want, once a month, to leave the process running in the
    background and collecting the processes

## Unreleased

## 0.1.0 — 2026-11-11

The first public version.

- **What is not audited wins the eye**: the process tree in three bands,
  `WEIRD`, `NEW` then `SAFE`, with an audit column; `NEW` is bold red.
- **Read-only by construction**: it reads `/proc`, never signals or writes to a
  process, and makes no network call.
- **Graduated trust**: `s` marks `trust`, `S` opens the picker (`core`, `safe`,
  `audited`, `trust`, `personal`, `watch`, `unsafe`).
- **Stable signatures**: name + resolved executable, plus the script for known
  interpreters.
- **A parent vouches only for its direct children**; terminals cover their
  shells, `exclusive` turns every other child `WEIRD`.
- **Provider groups**: `SAFE` is split by who ships a process, riskiest first,
  with the distribution named from `/etc/os-release`.
- **A bundled base audit, split by distribution scope and family**, overridden
  by the user's own layer in `$XDG_DATA_HOME`.
- **An append-only journal**: every change to the user's layer goes to
  `history.jsonl`; undo is a new line, never a rewrite.
- **Package integrity on demand**: package owner and `dpkg -V`, memoised in a
  disposable cache.
- **An agent CLI**: JSON `snapshot`, `rules`, `annotate` and `verify`, and the
  `audit` skill (`analyse`, `update`).
- **Suggestions, not trust, for optional programs**: a base `suggestions/`
  folder per family; the row shows `NEW sug`, `A` accepts it into your layer.
- **A demo machine**: `--demo` runs on a fictional host, and `just gif`
  records the README's GIF from it.
- **Hardening documented**: who can rewrite the audit, the options today, and
  the signed journal to come.
- **Empty slots for other distributions**, waiting for contributors.
