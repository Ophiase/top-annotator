from __future__ import annotations

from dataclasses import dataclass

LOOPBACK_PREFIXES = ("127.", "[::1]", "localhost")


def is_loopback(address: str) -> bool:
    return address.rsplit(" ", 1)[-1].startswith(LOOPBACK_PREFIXES)


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    pid: int
    ppid: int
    name: str
    exe: str
    cmdline: tuple[str, ...]
    user: str
    state: str
    threads: int
    rss_bytes: int
    cpu_percent: float
    signature: str
    unit: str = ""
    listens: tuple[str, ...] = ()

    @property
    def service(self) -> str:
        """The systemd service this process runs in, empty when it is not one."""
        return (
            self.unit.removesuffix(".service") if self.unit.endswith(".service") else ""
        )

    @property
    def exposed(self) -> bool:
        return any(not is_loopback(address) for address in self.listens)

    @property
    def command(self) -> str:
        return " ".join(self.cmdline) if self.cmdline else f"[{self.name}]"
