from pathlib import Path

from top_annotator.process.verify import (
    PackageIntegrity,
    VerificationCache,
    parse_modified,
    parse_owner,
)


def test_parse_owner_takes_the_first_package() -> None:
    output = "systemd-sysv: /sbin/init\nother: /sbin/init"

    assert parse_owner(output) == "systemd-sysv"


def test_parse_owner_keeps_a_multi_package_owner_readable() -> None:
    assert parse_owner("libc6, libc6-dev: /usr/include/x") == "libc6"


def test_parse_modified_keeps_real_dpkg_findings() -> None:
    output = (
        "??5??????   /usr/bin/tool\n"
        "missing     /usr/share/doc/tool\n"
        "??5?????? c /etc/tool.conf\n"
        "missing     /root/private (Permission denied)\n"
    )

    assert parse_modified(output) == (
        "??5??????   /usr/bin/tool",
        "missing     /usr/share/doc/tool",
    )


def test_verification_cache_round_trip(tmp_path: Path) -> None:
    executable = tmp_path / "tool"
    executable.write_text("binary", encoding="utf-8")
    cache = VerificationCache(tmp_path / "cache")
    integrity = PackageIntegrity(
        path=str(executable),
        package="tool",
        version="1.0",
    )
    cache.store(str(executable), integrity)

    reloaded = VerificationCache(tmp_path / "cache")

    assert reloaded.get(str(executable)) == integrity
    assert (tmp_path / "cache" / "verification.json").exists()


def test_package_integrity_summary_is_honest_about_unknowns() -> None:
    assert "no executable" in PackageIntegrity(path="").summary
    assert "not owned" in PackageIntegrity(path="/opt/tool").summary
    assert (
        "dpkg -V clean"
        in PackageIntegrity(
            path="/usr/bin/tool",
            package="tool",
            version="1.0",
        ).summary
    )
