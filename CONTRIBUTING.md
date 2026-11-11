# Contributing

Everything is written in English: code, comments, markdown and commits.

```sh
uv sync --all-groups
just gate
```

A change is ready when `just gate` passes. Read [AGENTS.md](AGENTS.md) and the
rules it links to; they apply to people as much as to agents.

## Adding a distribution

| Scope | State |
| --- | --- |
| `ubuntu` (GNOME) | audited |
| `pop` (COSMIC) | audited |
| `debian`, `fedora`, `arch`, `linuxmint`, `opensuse-tumbleweed` | empty slots with a `TODO` |

The base audit is split by distribution scope, then by family, under
`src/top_annotator/audit/base/`. A folder named after an `/etc/os-release` id
is read on that distribution only.

- Audit your own machine first: annotate in the TUI, then copy the generic
  entries into the scope's folder.
- Keep what every install of the distribution runs in the family folder.
- An optional program (a driver, a VPN, Docker) goes in the family's
  `suggestions/` folder: it is offered, never trusted.
- A program only your machine runs stays in your own layer.
- Keep each file under roughly 20 entries; never put one distribution's entry
  in another's folder.
- Treat what you submit as a fingerprint: no host name, user name or home path
  in a note.
