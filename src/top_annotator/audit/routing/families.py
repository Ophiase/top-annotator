from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ...core.process_info import ProcessInfo
from ...process.heuristics import looks_like_system_process

SYSTEM = "system"
COSMIC = "cosmic"
GNOME = "gnome"
PROGRAMS = "programs"
FAMILIES = (SYSTEM, COSMIC, GNOME, PROGRAMS)
FAMILIES_PATH = Path(__file__).with_name("families.yaml")


@dataclass(frozen=True, slots=True)
class FamilyConfig:
    cosmic_name_prefixes: tuple[str, ...]
    cosmic_paths: tuple[str, ...]
    gnome_name_prefixes: tuple[str, ...]
    gnome_paths: tuple[str, ...]
    program_paths: tuple[str, ...]

    @classmethod
    def load(cls, path: Path = FAMILIES_PATH) -> FamilyConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a mapping")
        return cls(
            cosmic_name_prefixes=_strings(payload, "cosmic_name_prefixes"),
            cosmic_paths=_strings(payload, "cosmic_paths"),
            gnome_name_prefixes=_strings(payload, "gnome_name_prefixes"),
            gnome_paths=_strings(payload, "gnome_paths"),
            program_paths=_strings(payload, "program_paths"),
        )


def _strings(payload: dict[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(value)


CONFIG = FamilyConfig.load()
COSMIC_NAME_PREFIXES = CONFIG.cosmic_name_prefixes
COSMIC_PATHS = CONFIG.cosmic_paths
GNOME_NAME_PREFIXES = CONFIG.gnome_name_prefixes
GNOME_PATHS = CONFIG.gnome_paths
PROGRAM_PATHS = CONFIG.program_paths


def family_for(process: ProcessInfo) -> str:
    """Where a new annotation belongs in the audit/ folder.

    The user can move the entry; this only keeps the common case out of the
    wrong file.
    """
    executable = process.exe or (process.cmdline[0] if process.cmdline else "")
    if executable.startswith(PROGRAM_PATHS):
        return PROGRAMS
    if process.name.startswith(COSMIC_NAME_PREFIXES):
        return COSMIC
    if executable.startswith(COSMIC_PATHS):
        return COSMIC
    if process.name.startswith(GNOME_NAME_PREFIXES):
        return GNOME
    if executable.startswith(GNOME_PATHS):
        return GNOME
    if looks_like_system_process(process):
        return SYSTEM
    return PROGRAMS
