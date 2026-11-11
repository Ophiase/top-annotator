from __future__ import annotations

import json
from pathlib import Path

from .package_integrity import PackageIntegrity


class VerificationCache:
    def __init__(self, directory: Path) -> None:
        self.path = directory / "verification.json"
        self.entries = _read_cache(self.path)

    def get(self, executable: str) -> PackageIntegrity | None:
        raw = self.entries.get(_cache_key(executable))
        if not isinstance(raw, dict):
            return None
        return PackageIntegrity(
            path=str(raw.get("path", executable)),
            package=str(raw.get("package", "")),
            version=str(raw.get("version", "")),
            modified=tuple(str(line) for line in raw.get("modified", [])),
            unavailable=str(raw.get("unavailable", "")),
        )

    def store(self, executable: str, integrity: PackageIntegrity) -> None:
        self.entries[_cache_key(executable)] = {
            "path": integrity.path,
            "package": integrity.package,
            "version": integrity.version,
            "modified": list(integrity.modified),
            "unavailable": integrity.unavailable,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.entries, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _cache_key(path: str) -> str:
    try:
        stat = Path(path).stat()
    except OSError:
        return f"v1|{path}||"
    return f"v1|{path}|{stat.st_size}|{stat.st_mtime_ns}"


def _read_cache(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
