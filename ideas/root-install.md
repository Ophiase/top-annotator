# Root install

**[sketch]** Today the user's layer and its journal are plain files in
`$XDG_DATA_HOME`: anything running as the user can rewrite them, including the
process being audited. A malicious program could mark itself `trust` and erase
the journal line that says so.

## The idea

Install `top-annotator` once as root, and make it the only way to change the
audit:

- the session and `history.jsonl` live in a root-owned directory such as
  `/var/lib/top-annotator/<user>/`, readable by the user, writable by root
  only;
- an unprivileged user changes them only through a small privileged entry
  point (a setuid-free helper started by polkit or a systemd socket), which
  validates the request and appends to the journal;
- the journal becomes a real transaction log: every change has an author, a
  time and the state before, and a user cannot rewrite the past, only add to
  it.

## Questions

- **[question]** polkit action or a systemd socket-activated helper? Both
  avoid setuid; polkit gives an authentication prompt for free.
- **[question]** Should the helper also hash-chain the journal lines, so a
  root-level edit outside the tool is at least detectable?
- **[caution]** A root helper is a new attack surface. It must parse the
  smallest possible request (signature, level, provider, note) and never run
  anything the request names.
- **[caution]** This protects the record against the user's own processes,
  not against root: see [robustness.md](robustness.md), level 5.
