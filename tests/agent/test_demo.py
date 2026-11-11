import os
from pathlib import Path

import pytest

from top_annotator.agent import paths_payload, snapshot_payload
from top_annotator.audit.routing import distribution_names
from top_annotator.audit.routing.os_release import OS_RELEASE_VARIABLE
from top_annotator.process.scan.demo import DemoMachine


def test_demo_machine_shows_every_band(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(OS_RELEASE_VARIABLE, "unset")
    machine = DemoMachine(tmp_path)
    payload = snapshot_payload(machine.store(), machine.scanner().scan())
    section = {row["signature"]: row["section"] for row in payload}

    assert section["kworkerd|/tmp/.ICE-unix/kworkerd"] == "WEIRD"
    assert section["sshd|/home/demo/.config/sshd"] == "WEIRD"
    assert section["sh|/usr/bin/dash|-c curl"] == "WEIRD"
    assert section["curl|/usr/bin/curl"] == "ATTENTION"
    assert section["wireplumber|/usr/bin/wireplumber"] == "NEW"
    assert section["claude|/home/demo/.local/bin/claude"] == "SAFE"


def test_demo_machine_names_a_fictional_distribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(OS_RELEASE_VARIABLE, "unset")
    DemoMachine(tmp_path).store()
    release = Path(os.environ[OS_RELEASE_VARIABLE])

    assert distribution_names(release) == {"distro": "debian", "derivative": "demo"}


def test_paths_name_every_place_and_who_can_write_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(OS_RELEASE_VARIABLE, "unset")
    places = paths_payload(DemoMachine(tmp_path).store(), None)
    names = {place["what"] for place in places}

    assert {"code", "base audit", "your layer", "journal", "os-release"} <= names
    assert all("writable_by_you" in place for place in places)
