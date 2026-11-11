from __future__ import annotations

import subprocess
from pathlib import Path

from .command_result import CommandResult
from .package_integrity import PackageIntegrity
from .verification_cache import VerificationCache


def inspect_executable(
    path: str,
    cache: VerificationCache | None = None,
) -> PackageIntegrity:
    if not path:
        return PackageIntegrity(path="")
    if not path.startswith("/"):
        return PackageIntegrity(path=path, unavailable="no absolute executable path")
    if cache is not None:
        cached = cache.get(path)
        if cached is not None:
            return cached
    package = _package_for(path)
    if not package:
        result = PackageIntegrity(path=path)
    else:
        version = _run(("dpkg-query", "-W", "-f=${Version}", package)).output.strip()
        verified = _run(("dpkg", "-V", package))
        result = PackageIntegrity(
            path=path,
            package=package,
            version=version,
            modified=parse_modified(verified.output),
            unavailable=verified.unavailable,
        )
    if cache is not None:
        cache.store(path, result)
    return result


def _run(command: tuple[str, ...]) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return CommandResult(unavailable=f"{command[0]} is not installed")
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(unavailable=str(error))
    output = result.stdout.strip() or result.stderr.strip()
    return CommandResult(output=output)


def _package_for(path: str) -> str:
    candidates = [path]
    for prefix, replacement in (
        ("/usr/bin/", "/bin/"),
        ("/usr/sbin/", "/sbin/"),
        ("/usr/lib/", "/lib/"),
    ):
        if path.startswith(prefix):
            candidates.append(replacement + path.removeprefix(prefix))
    resolved = str(Path(path).resolve(strict=False))
    if resolved not in candidates:
        candidates.append(resolved)
    for candidate in candidates:
        result = _run(("dpkg-query", "-S", candidate))
        if result.unavailable:
            return ""
        package = parse_owner(result.output)
        if package:
            return package
    return ""


def parse_owner(output: str) -> str:
    for line in output.splitlines():
        package, separator, path = line.partition(": ")
        if separator and package and path.startswith("/"):
            return package.split(",")[0].strip()
    return ""


def parse_modified(output: str) -> tuple[str, ...]:
    modified: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or "(Permission denied)" in stripped:
            continue
        fields = stripped.split()
        if len(fields) >= 3 and fields[1] == "c":
            continue
        modified.append(stripped)
    return tuple(modified)
