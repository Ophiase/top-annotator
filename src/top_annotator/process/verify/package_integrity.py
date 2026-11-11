from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PackageIntegrity:
    path: str
    package: str = ""
    version: str = ""
    modified: tuple[str, ...] = ()
    unavailable: str = ""

    @property
    def summary(self) -> str:
        if self.unavailable:
            return self.unavailable
        if not self.path:
            return "no executable path to check"
        if not self.package:
            return "not owned by a dpkg package"
        if self.modified:
            return f"{len(self.modified)} packaged file(s) differ from dpkg metadata"
        return f"package {self.package} {self.version}; dpkg -V clean"

    def detail(self) -> str:
        if not self.modified:
            return ""
        return "\n".join(self.modified[:5])
