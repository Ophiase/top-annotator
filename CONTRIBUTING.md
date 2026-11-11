# Contributing

**Do not fork this repository; copy it.** The project is decentralised:
there is no upstream to feed, and no pull request to wait for.

1. Clone it into a repository of your own, not a GitHub fork.
2. Let your agent maintain your copy for your machine and your threat model.
3. Make it public if you like. Other people's agents may list it in their
   `trust-repos.yaml`, read what you added, and port what they judge good.

Ideas travel between copies, reviewed by each owner; nobody merges anyone
else's code. Why: [docs/philosophy.md](docs/philosophy.md).

## Working on a copy

Everything is written in English: code, comments, markdown and commits.

```sh
uv sync --all-groups
just gate
```

A change is ready when `just gate` passes. Read [AGENTS.md](AGENTS.md) and the
rules it links to; they apply to people as much as to agents.

## Auditing a distribution

| Scope | State here |
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
- Treat what you publish as a fingerprint: no host name, user name or home
  path in a note.
