# Trust, provider and coverage

Two separate axes: the trust level says **how much** a process is trusted;
the provider says **who ships it**. Neither is derived from the other.

## Trust levels

The positive levels, lowest first:

| Level | Meaning |
| --- | --- |
| `trust` | I trust it enough; the fast `s` mark |
| `host` | the program is safe, what it spawns is reviewed: an editor, a browser |
| `audited` | I reviewed its behaviour |
| `safe` | package-managed and integrity-checked |
| `core` | kernel, PID 1, boot path: the highest trust |
| `personal` | a program we write ourselves, in violet |

- `watch` and `unsafe` are the negative levels and send the row to `WEIRD`.
- `s` sets `trust`; `S` opens the picker; `a` cycles every level.

## Provider

| Provider | Ships |
| --- | --- |
| `kernel` | kernel threads; set automatically |
| `systemd` | PID 1 and systemd's own daemons |
| `distro` | a package of the base distribution, unchanged: dbus, polkit, NetworkManager |
| `derivative` | a package the derivative makes or patches on its base |
| `desktop` | the session's plumbing: GNOME or COSMIC shell, settings, portals |
| `service` | a third-party program always up in the background: Docker, a VPN daemon |
| `app` | a program you drive and its helpers: a browser, an editor, a terminal |

- A terminal packaged by the distribution is still an `app`.
- A VPN's window is an `app`, its root daemon a `service`.
- The TUI names `distro` and `derivative` from `/etc/os-release`: `ID_LIKE`
  gives the base, `ID` the derivative, e.g. `distro (ubuntu)`.
- The line between them is the repository `apt-cache policy <package>` shows.
- An audit written with the older `pop` provider loads as `derivative`.

## Parents, children, daemons and GUIs

```yaml
  syncthing|/usr/bin/syncthing:
    category: safe
    children: [syncthing]
    exclusive: true
  alacritty|/home/me/.cargo/bin/alacritty:
    category: trust
    gui: true
    terminal: true
  yazi|/home/me/.cargo/bin/yazi:
    category: trust
    interactive: true
```

| Field | Effect |
| --- | --- |
| `children` | the child names this process vouches for, one level down only |
| `exclusive` | every other child goes `WEIRD`, labelled `UNEXPECTED` |
| `gui` | a desktop application you drive yourself |
| `terminal` | covers its shells (`bash`, `dash`, `fish`, `sh`, `zsh`), shown `shell` |
| `interactive` | expected only when typed in such a shell; anywhere else, `WEIRD` |
| `agent` / `agents` | an AI agent, or the children of a parent that are agents |
| `plugin_args` | the arguments of a plugin host: its shells are not covered |

- Coverage never reaches grandchildren: a terminal covers its shell, not what
  the shell runs.
- A shell with no entry goes `WEIRD` unless a parent, an agent or an accounted
  shell explains it.

## Columns from `/proc`

Two columns never come from an annotation:

| Column | Shows |
| --- | --- |
| `net` | `net` when listening on a non-loopback address, `lo` on loopback only |
| `kind` | `gui`, or the systemd service the process runs in |

Without root, another user's sockets stay invisible: a root daemon shows
nothing in `net`.
