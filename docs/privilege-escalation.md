# Privilege escalation

A program running as you can become root **without any exploit** when one of
the doors below is open. The sudo password protects you only while your
session is clean.

Some of these doors are programs you trust: a root Docker daemon is `SAFE`
software in a dangerous state. top-annotator shows the ones it can see from
a running process in the `ATTENTION` band; `Enter` explains why.

## What the screen catches

| Process | Shown when | Why it matters |
| --- | --- | --- |
| `dockerd`, `containerd`, `podman` | it runs as root and you can write its socket | ask it to mount `/` in a container: root |
| `libvirtd` | same | give a VM the host's disk: root |
| `lxd`, `incusd` | same | a privileged container mounting `/`: root |
| `Xorg`, `X` | it runs | every graphical app reads your keys, the sudo password included |

The socket paths are in `process/heuristics/attention.yaml`.

## What it cannot see

These are configuration, not processes; the `/full-audit` skill checks them:

- **Groups equivalent to root**: `docker`, `lxd`, `incus-admin`, `libvirt`,
  `disk` (raw reads of `/dev/sdX`), `input` (a global keylogger).
  `sudo` / `wheel` are root by definition, behind a password. `adm` only
  reads logs.
- **sudoers**: `NOPASSWD`, wildcards, or a command that opens a shell
  (`vim`, `less`, `find`, `tar`, `python`; see GTFOBins).
- **Unusual SUID / SGID binaries**, and file capabilities such as
  `cap_setuid`, `cap_dac_read_search`, `cap_sys_admin`.
- **Permissive polkit rules** in `/etc/polkit-1/rules.d`.
- **Something root runs that you can modify**: a systemd unit, a cron job, a
  script, or a folder in root's `PATH`.
- **A trapped shell**: an alias or a `PATH` entry in your shell config that
  puts a fake `sudo` first, to collect the password.

## Quick check

```bash
id -nG
sudo -l
ls -l /var/run/*.sock /run/*.sock 2>/dev/null
find / -xdev -perm -4000 -type f 2>/dev/null
getcap -r / 2>/dev/null
ls /etc/polkit-1/rules.d /etc/sudoers.d
echo "$XDG_SESSION_TYPE"
```

## Closing the common doors

| Door | Fix |
| --- | --- |
| Docker | never `usermod -aG docker $USER`; use rootless Docker (`dockerd-rootless-setuptool.sh install`), then disable and mask the root `docker.service` and `docker.socket` |
| Podman | rootless by default: keep it so, and do not expose the rootful `podman.socket` |
| LXD / Incus | the `incus` group (restricted projects) rather than `incus-admin` / `lxd`; unprivileged containers only |
| libvirt | `qemu:///session` rather than `qemu:///system`; stay out of the `libvirt` group |
| sudo | no `NOPASSWD` on a generic command or a wildcard; a fixed binary with fixed arguments you cannot modify |
| Session | Wayland rather than X11 |

- After moving Docker to rootless, check it:
  `docker run --rm -v /etc/shadow:/shadow:ro alpine cat /shadow` must say
  permission denied.
- Rootless Docker also stops published ports from bypassing the firewall.
- sudo protects you against what has not taken your user yet, not against
  what already has: see [hardening.md](hardening.md).
