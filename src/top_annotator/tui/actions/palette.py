from __future__ import annotations

from functools import partial

from textual.binding import Binding
from textual.command import DiscoveryHit, Hit, Hits, Provider


class TopAnnotatorCommands(Provider):
    """Every binding in the palette, plus the keyless freeze toggle."""

    async def discover(self) -> Hits:
        for name, action, help_text in self._entries():
            yield DiscoveryHit(
                name,
                partial(self.app.run_action, action),
                help=help_text,
            )

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for name, action, help_text in self._entries():
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    partial(self.app.run_action, action),
                    help=help_text,
                )

    def _entries(self) -> tuple[tuple[str, str, str], ...]:
        grouped: dict[str, Binding] = {}
        for binding in Binding.make_bindings(type(self.app).BINDINGS):
            if binding.action != "escape":
                grouped.setdefault(binding.action, binding)
        entries = [
            (_label(binding), action, binding.key)
            for action, binding in grouped.items()
        ]
        frozen = bool(getattr(self.app, "frozen", False))
        entries.append((
            "Resume refresh" if frozen else "Freeze refresh",
            "toggle_freeze",
            "pause or resume the automatic /proc scan",
        ))
        entries.append((
            "Refresh now",
            "refresh_now",
            "scan /proc once, even while frozen",
        ))
        entries.append((
            "Review rules",
            "show_review",
            "compare session overrides with the audit files",
        ))
        return tuple(entries)


def _label(binding: Binding) -> str:
    description = binding.description.strip()
    if description.startswith("[") and "]" in description:
        description = description.split("]", 1)[1].strip()
    return description or binding.action.replace("_", " ")
