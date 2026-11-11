# Reference projects

Read these before inventing a structure, a convention or a style. Their paths
are local and never tracked: put them in `.agents/local/projects.yaml`
(template: [local.example.yaml](local.example.yaml)). Read only; take the method, never
the content.

## TUI reference

A Python CLI with a mature Textual interface: vim bindings, tree rows, fuzzy
search, modal screens, a footer that explains the keys. This project borrows
the shape, not the code.

## Agent-layer reference

The source of the `.agents/` layout: project policy, guard, short topic rules,
files that say what a comment earns and what a file is allowed to become.

## Industrial Python reference

A small published Python tool: uv, just, Ruff, Ty, pytest, src layout,
`AGENTS.md` for every agent. The toolchain follows it.

## Before reusing

Read `.agents/guard.yaml` first. A missing guard is permissive, never
confidential. Never name, quote or describe a private reference in a tracked
file or a commit; refer to it by role only.
