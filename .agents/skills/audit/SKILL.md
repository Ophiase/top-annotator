---
name: audit
description: Look at what runs on this machine with top-annotator. `analyse` (the default) is a read-only look that ends in a post-it sized report of anything suspicious; `update` classifies the processes that are not annotated yet and writes them after the user agrees. Use when the user asks what runs, whether anything looks suspicious, or to classify, annotate or update the audit.
argument-hint: "[analyse|update]"
---

# Audit

Two modes on top of the agentic CLI described in `docs/agents.md`. Both run from
the repository root with `uv run top-annotator …`. Both are bound by the
invariants in `AGENTS.md`: read `/proc` only, never signal or kill, no
network.

Answer in the user's language; anything written to a file stays in English.

## Gather the evidence

Take one snapshot and keep working from that file, so the evidence does not
move under you:

```bash
snap=$(mktemp -d)/snapshot.json   # or a scratchpad path
uv run top-annotator snapshot > "$snap"
jq 'group_by(.section) | map({(.[0].section): length}) | add' "$snap"
```

What needs a look, one line per signature:

```bash
jq -r '[.[] | select(.section != "SAFE")] | unique_by(.signature) | .[]
  | [.section, (.weird // ""), .signature, .user, .service, .exposed]
  | @tsv' "$snap"
```

A `SAFE` process can still deserve a word. Also check:

- `exposed: true` (listens on a non-loopback address), whatever its section:
  `jq -r '.[] | select(.exposed) | [.signature, (.listens|join(","))] | @tsv'`;
- a `trust` / `host` process running as `root`;
- an executable under `/tmp`, `/var/tmp`, `/dev/shm`, or a deleted one;
  the snapshot puts these in `WEIRD` already.

For a process you want to judge, look before you decide:

- `uv run top-annotator verify <exe>`: the owning package and the `dpkg -V`
  differences. `package: ""` means no package owns the file;
- the parent chain: follow `ppid` in the snapshot;
- `ls -l /proc/<pid>/exe`, `cat /proc/<pid>/cmdline | tr '\0' ' '`,
  `systemctl --user status <service>` or `systemctl status <service>`.

Never read another process's memory or environment, and never attach a
debugger: the evidence above is enough to decide whether to escalate.

## analyse

Read-only: do not annotate, do not edit `audit/`.

Judge each candidate on these signals, strongest first:

1. an executable in a writable temporary directory, a deleted one, or a
   system name on the wrong binary (the snapshot's `weird` reason);
2. `dpkg -V` differences on a package-owned executable;
3. a non-packaged binary that runs as `root` or listens on the network;
4. an unannotated process with no clear parent: not started by a terminal,
   the session, a service or a known application;
5. a zombie or a short-lived helper: usually noise; say so in one word.

Then write the report so it fits a post-it: **at most six lines**, no
headings, no table.

```text
<verdict>: nothing alarming | worth a look | suspicious
<N> processes · <W> WEIRD · <U> not annotated · <E> exposed on the network
- <process>: <one-line reason>          (at most three lines like this)
Next: <the one thing to do, or "nothing">
```

The verdict is `suspicious` only on signals 1 to 3. An unknown but ordinary
user program (a CLI in `~/.local/bin`, a Flatpak app) is `worth a look` at
most. If nothing stands out, the report is two lines.

## update

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
  `<what it is>; shipped by the Pop!_OS/Ubuntu package \`<pkg>\` at
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
  (`ubuntu/`) for the rest. Then the family as `audit/routing/families.py`
  routes it (`system/`, `gnome/`, `cosmic/`, `programs/`), then the topic
  file; keep each file under about 20 entries and create a new topic file
  rather than overflowing one. Keep the existing entry order (sorted by
  signature) and keep the keys sorted alphabetically, as the writer does,
  with today's date in `updated`. Never move an
  existing entry to another family.

After writing, run `uv run top-annotator snapshot` again and report how many
processes are still unannotated. After a base edit, also run `just gate`.
Do not commit.
