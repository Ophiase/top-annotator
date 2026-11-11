# Background trace

**[sketch]** A snapshot misses what lives briefly: a timer's job, a `curl`
of 200 ms, a binary that starts and deletes itself. That is exactly how a
quiet intruder behaves.

## The idea

- `top-annotator record --every 2s --for 24h`, started by a systemd user
  timer once a month rather than a daemon of its own.
- It writes a JSONL trace: one line per signature **first seen**, with the
  parent chain, the user, the service and whether it listened; then a last
  seen time. Duplicates are folded; nothing is annotated.
- [argument-bound](argument-bound.md) programs are recorded per invocation,
  with their arguments.
- `/analyse --trace <file>` reads it: what appeared over the period, what is
  new since the last trace, what ran once and vanished.

## Limits

- **[caution]** Polling every 2 s misses what lives less than 2 s. Only the
  kernel's process connector or eBPF see every `exec`, and both need root.
- **[caution]** The trace is a fingerprint of the machine and a target: it
  lives in the data folder, append-only like `history.jsonl`, and is never
  shared as is.

## Questions

- **[question]** Polling first, an `exec` source as root later, behind the
  same trace format?
- **[question]** Keep every trace, or only the diff against the previous
  one?
