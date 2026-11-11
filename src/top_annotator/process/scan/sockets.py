from __future__ import annotations

import os
from pathlib import Path

TCP_LISTEN = "0A"
UDP_UNCONNECTED = "07"
TABLES = (
    ("tcp", TCP_LISTEN),
    ("tcp6", TCP_LISTEN),
    ("udp", UDP_UNCONNECTED),
    ("udp6", UDP_UNCONNECTED),
)


def listening_sockets(proc: Path) -> dict[str, str]:
    """Socket inode to `proto address:port`, for every listening socket."""
    sockets: dict[str, str] = {}
    for table, state in TABLES:
        try:
            lines = (proc / "net" / table).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines[1:]:
            fields = line.split()
            if len(fields) > 9 and fields[3] == state:
                local = decode_address(fields[1])
                sockets[fields[9]] = f"{table.removesuffix('6')} {local}"
    return sockets


def listens_of(process_directory: Path, sockets: dict[str, str]) -> tuple[str, ...]:
    """Unreadable for another user's process without root: then empty."""
    found: set[str] = set()
    try:
        with os.scandir(process_directory / "fd") as entries:
            for entry in entries:
                try:
                    target = str(Path(entry.path).readlink())
                except OSError:
                    continue
                if target.startswith("socket:["):
                    address = sockets.get(target[8:-1])
                    if address is not None:
                        found.add(address)
    except OSError:
        return ()
    return tuple(sorted(found))


def decode_address(raw: str) -> str:
    host, port = raw.split(":")
    if len(host) == 8:
        octets = bytes.fromhex(host)[::-1]
        return f"{'.'.join(str(octet) for octet in octets)}:{int(port, 16)}"
    return f"[{_ipv6(host)}]:{int(port, 16)}"


def _ipv6(host: str) -> str:
    words = b"".join(
        bytes.fromhex(host[index : index + 8])[::-1] for index in range(0, 32, 8)
    )
    if words == bytes(16):
        return "::"
    if words == bytes(15) + b"\x01":
        return "::1"
    if words[:12] == bytes(10) + b"\xff\xff":
        return "::ffff:" + ".".join(str(octet) for octet in words[12:])
    groups = [words[index : index + 2].hex() for index in range(0, 16, 2)]
    return ":".join(group.lstrip("0") or "0" for group in groups)
