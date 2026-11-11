# Python

The portable rules are in
[../portable/rules/python.md](../portable/rules/python.md), with
[../portable/rules/python-remarks.md](../portable/rules/python-remarks.md) for
the failure modes. This project adds:

- Type annotations everywhere, including test helpers.
- `dataclass(frozen=True, slots=True)` for internal value objects. A public
  boundary may use pydantic, but this project has none.
- Modern syntax the project allows: `tuple[T, ...]` for immutable sequences,
  `Self` in classmethods, `X | None`, structural `Protocol` only at a seam the
  project does not own.
- Short functions. Split a file when it collects several concerns; `app.py` is
  allowed to be the composition point, not a dumping ground.
- A comment records a **why** the code cannot express. Do not narrate the code,
  do not add module headers.
- Names say what a value means; no single letters, no invented abbreviations.
- Pure logic belongs in `tree.py`, `signature.py`, `audit.py`: the tests should
  not need a terminal.
- A UI action must never block for long. `/proc` scanning is small; if a new
  feature adds I/O, move it off the UI thread.
- Never suppress a finding with a bare `# noqa`; fix it or explain the rule on
  the same line.
