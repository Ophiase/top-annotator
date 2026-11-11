# ideas — map

One concept per file, short. Tags: **[defined]**, **[sketch]**,
**[question]**, **[caution]**.

The thesis: a process monitor should not ask only "do I trust this name?".
It must answer two separate questions:

- **identity confidence** — do I know what this executable really is?
- **trust decision** — do I accept what it does?

`audit/` records the second; package ownership, hashes and signatures raise the
first. Keeping them apart stops "safe" from meaning both "known" and "good".

- [robustness.md](robustness.md) — checks, limits, tool crossovers
- [root-install.md](root-install.md) — a root-owned audit only the tool can
  change
- [signed-journal.md](signed-journal.md) — a hash-chained journal only the
  user's key can sign
- [background-trace.md](background-trace.md) — record what appears over a
  day, for an agent to read
- [argument-bound.md](argument-bound.md) — programs like `curl` whose meaning
  is in their arguments
- [signature-spoofing.md](signature-spoofing.md) — where a process chooses
  part of its own identity
