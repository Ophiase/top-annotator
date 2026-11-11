# Demo mode

A real process list is a fingerprint of a machine. Demo mode runs everything
on a bundled fictional one instead.

```bash
top-annotator --demo              # the TUI
top-annotator --demo snapshot     # the JSON an agent reads
```

- The user, the distribution (`Demo Linux`, derived from Debian) and the
  programs are invented; addresses are documentation ranges.
- Your annotations go to a temporary folder, discarded on exit: every run
  starts from the same state.
- It never reads `/proc`, your audit or your `/etc/os-release`.

## What it shows

| Band | Process | Why |
| --- | --- | --- |
| `WEIRD` | `kworkerd` | a kernel-looking name running from `/tmp` |
| `WEIRD` | `sshd` | a system name outside the system directories |
| `WEIRD` | `sh -c curl …` | a shell under a web server that should spawn only its workers |
| `WEIRD` | `thumbnailer` | a zombie |
| `ATTENTION` | `curl` from a cron job | legitimate perhaps, but what it does is in its arguments |
| `NEW` | `wireplumber`, `gsd-color` | unannotated, with the `sys?` hint |
| `SAFE` | `claude` and its shells | an agent, and the shells it runs |

The fixture is in `src/top_annotator/process/scan/demo/`.

## Regenerating the GIF

```bash
just gif    # -> docs/media/demo.gif
```

- `tools/record_demo/` drives the TUI headlessly on the demo machine and
  saves Textual's own SVG export for each frame.
- `cairosvg` rasterizes the frames; ImageMagick's `convert` assembles the GIF.
- The recorder fails if the details screen does not open, so a mute
  recording cannot ship.
- It never presses `Enter` on a real system path: `dpkg` would answer with the
  recording machine's package versions.
