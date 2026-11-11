from __future__ import annotations

import os
import shlex
from functools import cache
from pathlib import Path

OS_RELEASE = Path("/etc/os-release")
OS_RELEASE_VARIABLE = "TOP_ANNOTATOR_OS_RELEASE"
COMMON_SCOPE = "common"


def os_release_path() -> Path:
    override = os.environ.get(OS_RELEASE_VARIABLE)
    return Path(override) if override else OS_RELEASE


@cache
def distribution_names(path: Path | None = None) -> dict[str, str]:
    """This machine's names for the generic providers, from os-release:
    Pop!_OS (`ID=pop`, `ID_LIKE=ubuntu debian`) gives `distro` → ubuntu and
    `derivative` → pop; plain Ubuntu or Arch gives only `distro`."""
    fields = read_os_release(path or os_release_path())
    identifier = fields.get("ID", "")
    bases = fields.get("ID_LIKE", "").split()
    if bases and identifier:
        return {"distro": bases[0], "derivative": identifier}
    return {"distro": identifier} if identifier else {}


@cache
def active_scopes(path: Path | None = None) -> tuple[str, ...]:
    """The base audit folders this machine reads: `common`, then its own
    distribution and the ones it derives from (`pop`, `ubuntu`, `debian`)."""
    fields = read_os_release(path or os_release_path())
    names = [fields.get("ID", ""), *fields.get("ID_LIKE", "").split()]
    return (COMMON_SCOPE, *dict.fromkeys(name for name in names if name))


def read_os_release(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() and not key.startswith("#"):
            try:
                fields[key.strip()] = " ".join(shlex.split(value))
            except ValueError:
                continue
    return fields
