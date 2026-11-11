# Signatures and confidence

## What a signature is

An annotation must survive a restart, so it is keyed by a signature, not a PID:

```text
process name | executable [| script]
```

- The executable is the resolved `/proc/<pid>/exe` when readable.
- When the kernel hides that link from an unprivileged reader, `argv[0]` is
  used: `systemd` becomes `systemd|/sbin/init`.
- The script keeps every Python or Node program from sharing one annotation.
- Inline code (`sh -c …`) changes on every run: only `-c` and its first word
  are kept, so `sh -c kitty` stays distinct from `sh -c firefox`.

```text
gsd-xsettings|/usr/libexec/gsd-xsettings
python3|/usr/bin/python3|/home/me/bin/backup.py
kthreadd|kthreadd
zsh|/usr/bin/zsh|-c source
```

The format is stable: changing it breaks every existing annotation.

## The `sys?` hint

An unannotated process gets a small blue `sys?` next to `NEW` when:

- its executable lives in a system directory (`/usr/libexec`, `/usr/bin`,
  `/usr/lib`, `/nix/store`, …), or
- its name matches a known system prefix (`gsd-`, `xdg-`, `pipewire`, …).

It is a hint, never an automatic `safe`. You still decide.

## How confidence is layered

A base entry marked `safe` names the package that ships the executable. That
is convenient, not a proof. The levels, weakest first:

| Level | Evidence | What it misses |
| --- | --- | --- |
| 1 | the name | anything can be called `gsd-color` |
| 2 | path + name (`sys?`) | a binary dropped into `/usr/libexec` |
| 3 | package ownership (`dpkg-query -S`) | a file replaced in place |
| 4 | package integrity (`dpkg -V`, shown by `Enter`) | a replacement that also rewrote dpkg's metadata |
| 5 | a real trust boundary: signed metadata, `debsums`, dm-verity, a known-good hash | a compromised kernel |

Past level 5 the question is no longer "is this binary legitimate?" but "is
the machine compromised?".

Identity ("is this really `systemd`?") and trust ("do I accept what it
does?") stay two axes: see [ideas/robustness.md](../ideas/robustness.md).
