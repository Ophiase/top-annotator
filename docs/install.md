# Install

top-annotator is at 0.1.x: it works on the author's workstation, the audit
format may still move, and nothing is published yet. Package managers come if
people need them; today, run it from the repository.

## At a glance

| Way | Status | For whom |
| --- | --- | --- |
| [From a clone](#from-a-clone) with uv | works, tested on Ubuntu-based Linux | anyone at ease with a terminal |
| [Installed from a clone](#installed-from-a-clone) | works | to have the command everywhere |
| [Straight from git](#straight-from-git) with `uvx` | works | to try it once |
| [Hardened](#hardened) | manual, see the guide | a machine you actually protect |
| [Not yet](#not-yet) | PyPI, distribution packages | everyone, later |

## Requirements

| Need | Why | Without it |
| --- | --- | --- |
| Linux | it reads `/proc` | nothing works |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | fetches Python 3.14 and the dependencies | install Python 3.14 yourself |
| [just](https://just.systems) | the recipes below | type the `uv` commands |
| `dpkg` | package owner and `dpkg -V` in the details screen | the integrity row stays empty |
| `wl-copy` | `y` copies to the Wayland clipboard | OSC 52 is used instead |

## From a clone

```sh
git clone https://github.com/Ophiase/top-annotator
cd top-annotator
uv run top-annotator
```

The first run downloads Python 3.14 if needed, then starts in a second.

## Installed from a clone

```sh
uv tool install .               # a copy: later edits to the clone do not apply
just install                    # editable: your edits apply at once
```

An editable install runs the code of your clone, which any process running as
you can modify. Prefer the copy on a machine you protect.

## Straight from git

```sh
uvx --from git+https://github.com/Ophiase/top-annotator top-annotator
```

Pin a commit with `@<sha>` at the end of the URL: the audit format may move.

## Hardened

Install a copy into a root-owned directory and keep the audit out of your
user's reach. The options and their limits are in [hardening.md](hardening.md).

## Not yet

If the project finds users:

- `uv tool install top-annotator` and `pipx install top-annotator` (PyPI);
- a signed release with a checksum;
- distribution packages.

Until then, read the code you run, or ask your agent to: see
[philosophy.md](philosophy.md).
