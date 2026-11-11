from pathlib import Path

import pytest

from top_annotator.core.annotation import Annotation
from top_annotator.core.category import Category
from top_annotator.core.section import Section, section_for
from top_annotator.process.heuristics import AttentionConfig, attention_reason

from ..factories import process

SAFE = Annotation(category=Category.SAFE)


def test_curl_never_fades_even_when_annotated() -> None:
    curl = process(9, 1, name="curl", exe="/usr/bin/curl", cmdline=("curl", "-s"))
    assert section_for(curl, SAFE, None) is Section.ATTENTION


def test_a_shell_running_curl_needs_attention() -> None:
    shell = process(
        9, 1, name="sh", exe="/usr/bin/dash", cmdline=("sh", "-c", "curl x")
    )
    assert "curl" in (attention_reason(shell) or "")


def test_a_shell_running_an_ordinary_command_does_not() -> None:
    shell = process(
        9, 1, name="zsh", exe="/usr/bin/zsh", cmdline=("zsh", "-c", "just test")
    )
    assert attention_reason(shell) is None


def test_inline_python_needs_attention() -> None:
    python = process(
        9, 1, name="python3", exe="/usr/bin/python3.14", cmdline=("python3", "-c", "x")
    )
    assert attention_reason(python) is not None


def test_a_root_daemon_with_a_writable_socket_is_a_danger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    socket = tmp_path / "docker.sock"
    socket.touch()
    config = AttentionConfig.load()
    monkeypatch.setitem(config.root_sockets, "dockerd", (str(socket),))
    daemon = process(9, 1, name="dockerd", exe="/usr/bin/dockerd", user="root")

    assert "privilege escalation" in (config.reason(daemon) or "")


def test_a_rootless_daemon_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    socket = tmp_path / "docker.sock"
    socket.touch()
    config = AttentionConfig.load()
    monkeypatch.setitem(config.root_sockets, "dockerd", (str(socket),))
    daemon = process(9, 1, name="dockerd", exe="/usr/bin/dockerd", user="me")

    assert config.reason(daemon) is None
