# Signed journal

**[sketch]** Today `history.jsonl` is append-only by convention. A process
running as the user can rewrite it, and the tool cannot tell.

## The idea

Make every change to the user's layer carry a proof that the user made it:

- each journal line holds the hash of the previous line, so a rewrite of the
  past breaks the chain;
- each line is signed with a key only the user can use: `ssh-keygen -Y sign`
  with an SSH key, or a FIDO key that needs a touch;
- `session.yaml` becomes a view rebuilt from the verified journal, never a
  source of truth on its own;
- an entry whose chain or signature fails is shown `WEIRD`, never trusted.

## Agents

An agent's `annotate` appends an **unsigned proposal**. The TUI lists the
pending proposals; one key signs the ones the human accepts. A proposal
never changes what the screen trusts.

## Questions

- **[question]** `ssh-keygen -Y` (no new dependency, an external command) or a
  Python signing library? The first keeps the tool small.
- **[question]** One signature per line, or per session (a batch of lines)?
  Per session asks for one touch, not one per keystroke.
- **[question]** How is the base audit signed: the release tag, or a detached
  signature shipped with the files?
- **[caution]** A key loaded in `ssh-agent` signs for any process running as
  the user. Only a touch (`ed25519-sk`, `-O verify-required`) or a passphrase
  each time is a boundary.
- **[caution]** The verifier must not be writable by the user, or the check is
  theatre: see [root-install.md](root-install.md).
