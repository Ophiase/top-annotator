---
name: audit
description: Update the local audit with top-annotator. Runs the `analyse` skill first, then proposes a trust level, provider and note for each process that is not annotated yet, and writes them only after the user agrees. Use when the user asks to classify, annotate or update the audit.
---

# Audit

Updates the audit on top of the agentic CLI described in `docs/agents.md`.
Run it from the repository root with `uv run top-annotator …`. Bound by the
invariants in `AGENTS.md`: read `/proc` only, never signal or kill, no
network.

Answer in the user's language; anything written to a file stays in English.

## First, analyse

Run the `analyse` skill first and show its report. If its verdict is
`suspicious`, stop there: the user decides before anything gets trusted.
Reuse its snapshot for what follows.

## Classify

Classify the processes that have no annotation and are not covered by a
parent (`trust == null`, `covered_by_parent == false`, not a kernel thread).
Group them by signature first; one decision per signature.

When the snapshot carries `suggested`, the base offers a level for an
optional program. Start from it, check it against `verify` like any other
proposal, and say it came from the base; a suggestion is not evidence.

For each one, collect `verify`, the parent and the service, then propose:

- **trust level**, never higher than the evidence supports:
  - `safe` only for a package-owned executable with a clean `dpkg -V`;
  - `core` only for PID 1, the kernel path and the boot chain;
  - `host` for an editor, browser or terminal whose children are judged
    on their own; add `terminal: true` for a terminal;
  - `trust` for a program the user clearly runs themselves but that is
    not package-managed (`~/.local/bin`, `~/.cargo/bin`, Flatpak);
  - leave it **unannotated** when you cannot tell. Never `watch` or
    `unsafe` on your own: report it instead.
  The `sys?` hint is never enough for `safe`.
- **provider**, what it is or who ships it:
  `app` (a program the user drives, and its helpers), `service` (a
  third-party program always up in the background: a daemon, a VPN, a sync
  or tray helper), `desktop` (GNOME or COSMIC plumbing), `derivative`, `distro`,
  `systemd`, `kernel`. For the system part, `apt-cache policy <package>`
  decides between `distro` (the base distribution, unchanged) and
  `derivative` (made or patched by the derivative): on Pop!_OS,
  `apt.pop-os.org/ubuntu` or an Ubuntu mirror is `distro`,
  `apt.pop-os.org/release` is `derivative`.
- **note**, in the base's style:
  `<what it is>; shipped by the <distribution> package \`<pkg>\` at
  \`<path>\`. Package-managed, so \`dpkg -V <pkg>\` is the integrity check.`
  For a program that is not packaged, say where it comes from and why it
  runs.
- **parent flags** when they fit: `children`, `exclusive`, `gui`,
  `terminal`, `interactive`, `agents` (see the README).

Show the proposal as one compact table (signature, level, provider, one-line
reason) plus the list of what you left unannotated and why. Then ask where to
write it, unless the user already said:

- **session** (local to this user): one call per signature,

  ```bash
  uv run top-annotator annotate '<signature>' <level> \
    --provider <provider> --note '<note>' [flags]
  ```

- **base** (versioned, shared with the project): edit the YAML under
  `src/top_annotator/audit/base/`. Pick the scope first: `common/` for what
  is true on any distribution (a Flatpak), the derivative's folder (`pop/`)
  for a `derivative` entry or one it ships, the base distribution's folder
  (`ubuntu/`) for the rest. An optional program (a driver, a VPN, Docker)
  goes in the family's `suggestions/` folder instead: offered, never
  trusted. Then the family as `audit/routing/families.py`
  routes it (`system/`, `gnome/`, `cosmic/`, `programs/`), then the topic
  file; keep each file under about 20 entries and create a new topic file
  rather than overflowing one. Keep the existing entry order (sorted by
  signature) and keep the keys sorted alphabetically, as the writer does,
  with today's date in `updated`. Never move an
  existing entry to another family.

After writing, run `uv run top-annotator snapshot` again and report how many
processes are still unannotated. After a base edit, also run `just gate`.
Do not commit.
