from __future__ import annotations

from rich.style import Style
from rich.text import Text

from ..audit.routing import distribution_names
from ..core import (
    PROVIDERS,
    Annotation,
    Category,
    ProcessInfo,
    SectionHeader,
    provider_of,
)
from ..core.annotation import SHELLS
from ..core.tree.groups import KERNEL_FAMILIES
from ..process.heuristics import (
    is_kernel_thread,
    is_zombie,
    looks_like_system_process,
)

CATEGORY_COLORS: dict[Category, str] = {
    Category.TRUST: "#2f7d4e",
    Category.HOST: "#2f6f8a",
    Category.AUDITED: "#2f6f6a",
    Category.SAFE: "#1f7a4d",
    Category.CORE: "bold #145c3a",
    Category.PERSONAL: "bold #7b3fa0",
    Category.WATCH: "#9a6b1f",
    Category.UNSAFE: "bold #a33a3a",
}


PROVIDER_COLORS: dict[str, str] = {
    "kernel": "dim #1f5fa8",
    "systemd": "#3b5b8c",
    "distro": "#7a5c3e",
    "derivative": "#b0562a",
    "desktop": "#5b6f2f",
    "app": "#8a4a7a",
    "service": "#2e7d7d",
}


BAND_STYLE = Style(bold=True, color="#fffaf0", bgcolor="#3d3a33")
GROUP_STYLE = Style(bgcolor="#e4dccb", underline=True)


def header_style(header: SectionHeader) -> Style:
    """A band is a dark bar; a provider group a tinted, underlined line."""
    return GROUP_STYLE if header.group else BAND_STYLE


UNREVIEWED = "unreviewed"
TRUST_LABELS: dict[str, str] = {
    Category.CORE: "CORE — kernel / PID 1 / boot path",
    Category.SAFE: "SAFE — package-managed and verified",
    Category.AUDITED: "AUDITED — I reviewed its behaviour",
    Category.HOST: "HOST — safe itself; what it spawns is reviewed",
    Category.TRUST: "TRUST — I trust it (lowest level)",
    Category.PERSONAL: "PERSONAL — we wrote it",
    Category.WATCH: "WATCH — keep an eye on it",
    Category.UNSAFE: "UNSAFE — do not trust",
    UNREVIEWED: "UNREVIEWED — remove the annotation",
}


BAND_MEANINGS: dict[str, str] = {
    "WEIRD": "a pattern that deserves a human look, or marked watch / unsafe",
    "NEW": "userland processes nobody has reviewed yet",
    "SAFE": "every positive trust level, plus kernel threads",
    "unlabelled": "trusted, but nobody recorded its provider yet: run /audit update",
}


def group_title(header: SectionHeader) -> str:
    """The group's name, with this machine's distribution in parentheses."""
    name = header.group.rsplit("/", 1)[-1] or header.section.value
    local = distribution_names().get(header.group)
    return f"{name} ({local})" if local else name


def group_meaning(header: SectionHeader) -> str:
    name = header.group.rsplit("/", 1)[-1] or header.section.value
    if "/" in header.group:
        return KERNEL_FAMILIES.get(name, ((), "other kernel threads"))[1]
    return PROVIDERS.get(name) or BAND_MEANINGS.get(name, "")


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.0f}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}T"


def short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def audit_cell(
    annotation: Annotation | None,
    process: ProcessInfo,
    parent: Annotation | None = None,
    *,
    agent_shell: bool = False,
    suggested: bool = False,
) -> Text:
    if is_zombie(process):
        return Text("ZOMBIE", style="#9a6b1f")
    if parent is not None and parent.forbids(process.name):
        return Text("UNEXPECTED", style="bold #a33a3a")
    if annotation is None and parent is not None and parent.covers(process.name):
        label = "shell" if parent.terminal and process.name in SHELLS else "child"
        return Text(label, style="#2f7d4e")
    if annotation is None and agent_shell:
        return Text("agent", style="#7b3fa0")
    if annotation is None:
        if is_kernel_thread(process):
            return Text("kernel", style="dim #1f5fa8")
        cell = Text("NEW", style="bold #b42318")
        if suggested:
            cell.append(" sug", style="#7b5e1f")
        elif looks_like_system_process(process):
            cell.append(" sys?", style="#1f5fa8")
        return cell
    return Text(
        annotation.category.value.upper(),
        style=CATEGORY_COLORS[annotation.category],
    )


def provider_cell(process: ProcessInfo, annotation: Annotation | None) -> Text:
    provider = provider_of(process, annotation)
    return Text(provider, style=PROVIDER_COLORS.get(provider, "dim"))


def net_cell(process: ProcessInfo) -> Text:
    if process.exposed:
        return Text("net", style="bold #9a6b1f")
    if process.listens:
        return Text("lo", style="dim")
    return Text("")


def kind_cell(process: ProcessInfo, annotation: Annotation | None) -> Text:
    if annotation is not None and annotation.gui:
        return Text("gui", style="bold #2f6f6a")
    if not process.service:
        return Text("")
    name = process.service.removeprefix("app-").replace("@autostart", " (autostart)")
    return Text(short(name, 22), style="#7a5c3e")
