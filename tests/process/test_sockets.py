from __future__ import annotations

from pathlib import Path

from top_annotator.process.scan.sockets import (
    decode_address,
    listening_sockets,
    listens_of,
)
from top_annotator.process.scan.units import read_unit, unescape

COLUMNS = "st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode"
HEADER = f"  sl  local_address rem_address {COLUMNS}\n"
QUEUES = "00000000:00000000 00:00000000 00000000  1000        0"
LISTEN = f"   0: 00000000:C352 00000000:0000 0A {QUEUES} 4242 1\n"
ESTABLISHED = f"   1: 0100007F:1F90 0100007F:D431 01 {QUEUES} 4343 1\n"


def fake_proc(tmp_path: Path) -> Path:
    net = tmp_path / "net"
    net.mkdir()
    (net / "tcp").write_text(HEADER + LISTEN + ESTABLISHED, encoding="utf-8")
    return tmp_path


def test_ipv4_is_decoded() -> None:
    assert decode_address("0100007F:2BCB") == "127.0.0.1:11211"


def test_ipv6_any_and_loopback() -> None:
    assert decode_address("00000000000000000000000000000000:01BD") == "[::]:445"
    assert decode_address("00000000000000000000000001000000:0277") == "[::1]:631"


def test_only_listening_sockets_are_kept(tmp_path: Path) -> None:
    assert listening_sockets(fake_proc(tmp_path)) == {"4242": "tcp 0.0.0.0:50002"}


def test_process_listens_through_its_fds(tmp_path: Path) -> None:
    process_directory = tmp_path / "1234"
    fds = process_directory / "fd"
    fds.mkdir(parents=True)
    (fds / "3").symlink_to("socket:[4242]")
    (fds / "4").symlink_to("socket:[9999]")
    (fds / "5").symlink_to("/dev/null")
    sockets = listening_sockets(fake_proc(tmp_path))
    assert listens_of(process_directory, sockets) == ("tcp 0.0.0.0:50002",)


def test_unreadable_fds_mean_unknown(tmp_path: Path) -> None:
    assert listens_of(tmp_path / "missing", {}) == ()


def test_unit_is_the_last_cgroup_component(tmp_path: Path) -> None:
    (tmp_path / "cgroup").write_text(
        "0::/system.slice/ollama.service\n", encoding="utf-8"
    )
    assert read_unit(tmp_path) == "ollama.service"


def test_systemd_escapes_are_decoded() -> None:
    assert unescape("app-print\\x2dapplet@autostart.service") == (
        "app-print-applet@autostart.service"
    )
