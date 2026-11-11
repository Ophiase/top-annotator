# Signature spoofing

**[defined]** A signature is name + executable [+ script]. Two of its
fallbacks let a process choose part of its own identity.

## `argv[0]` for root processes

- An unprivileged reader cannot resolve `/proc/<pid>/exe` of a root
  process, so the signature falls back to `argv[0]`.
- `argv[0]` is written by the process. A root program started as
  `/usr/sbin/cron` gets `cron|/usr/sbin/cron`, the trusted signature.
- **[sketch]** Mark such a signature with an `argv0?` hint, and never let it
  reach `SAFE` on its own; `sudo top-annotator snapshot` resolves the real
  executable.
- **[caution]** A root attacker can also lie through `/proc`; the hint only
  removes the free lie.

## Inline commands

- Inline code keeps only `-c` and its first word, so `sh|/usr/bin/dash|-c
  curl` covers every pipeline that starts with `curl`.
- **[sketch]** When the first word is
  [argument-bound](argument-bound.md), the shell is argument-bound too.

## Name truncation

- **[defined]** The kernel name is 15 characters: `systemd-journal` is the
  name of `systemd-journald`. Two programs sharing a long prefix share a
  name; the executable path keeps them apart, so a name alone must never be
  trusted.

The `full-audit` skill checks each of these on a running machine.
