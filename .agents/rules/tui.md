# TUI

The interface is a `textual` app. Keep it boring and fast.

## Bindings

Vim first: `j`/`k` move, `g`/`G` jump, `h`/`l` fold, `space` toggles,
`/` searches, `q` quits. Arrow keys are aliases, not the primary path.
Do not take a key that a terminal or a user's muscle memory already owns
without a reason.

Every binding that matters daily is in the footer and in the README table.
Hidden bindings are for shortcuts, not for discovering the tool.

## Annotations

- `s` marks `trust` without a dialog; the fast path must stay one key.
- `A` accepts the base's suggestion; nothing else turns a suggestion into
  trust.
- `a` cycles all categories and ends on unannotated.
- `n` is the only modal that edits a note. It must preserve the category.
- After a change, re-render from the current scan; do not rescan just to paint.

## Search

`/` uses `textual.fuzzy.Matcher`. Results keep their full ancestor chain, and
the tree remains a tree: indentation, fold markers and branch guides must stay
correct when a filter is active. The `f` filters (`unreviewed`, `network`)
follow the same rule.

## Rendering

- One row per process, one line each.
- Band and provider-group headers are rows too: the cursor stops on them and
  `space`/`h`/`l` fold them. A fold is keyed by its band or group, never by
  PID alone.
- `NEW` is the loudest cell on the screen.
- Memory and CPU are right-aligned; command is dim and truncated.
- The status bar answers: how many shown, how many unreviewed, how many safe,
  and which modes are active.

## Safety

No terminate, kill, signal, nice or priority action. This is an observation
tool, not a process manager.
