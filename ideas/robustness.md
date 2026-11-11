# Robustness

## Two axes, never one score

**[defined]** An audit entry carries a *trust decision*. It says nothing about
whether the bytes on disk are the ones the package shipped.

| Axis | Question | Evidence |
| --- | --- | --- |
| Identity | is this really `systemd`? | path, package owner, hash, signature, IMA |
| Trust | do I accept what it does? | human decision, note, review date |

A `core` process with a broken identity is worse than an unknown process: it
looks legitimate. The UI should never collapse the two.

## What Linux gives locally

**[defined]** `dpkg -V` compares files with the md5 metadata recorded at
install time. It catches an in-place replacement that did not also rewrite
dpkg's metadata. It is not a signature: root can rewrite both.

**[sketch]** Better layers, in order of cost:

- `debsums` against a trusted package list;
- IMA appraisal / measurement, if the firmware and kernel enforce it;
- dm-verity or a read-only root;
- signed repository metadata, verified at install time;
- an external known-good hash.

No local check survives a fully compromised kernel. At that point the question
becomes "is the machine compromised?", not "is this binary safe?".

## Tool crossovers

**[defined]** These are different jobs; do not turn the TUI into a scanner.

| Tool | Worth it here? | Why |
| --- | --- | --- |
| ClamAV | later, optional | file/USB malware signatures; not process identity |
| Lynis | separate run | host hardening audit, not live monitoring |
| rkhunter / chkrootkit | occasional | noisy rootkit heuristics; old signals |
| YARA | later, promising | rules over suspicious binaries, not a trust database |
| Maldet | no | hosting/VPS malware scanning, wrong target |
| Wireshark | no | network analysis, outside process trust |

The first integration worth doing is **YARA on a selected binary**, because it
attaches evidence to a signature instead of adding another dashboard. ClamAV
can follow for downloaded files. The rest stay external commands that an agent
can run and explain.
