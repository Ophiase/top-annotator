from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .audit import AuditStore
from .audit.journal import HISTORY_FILENAME
from .audit.routing.families import FAMILIES_PATH
from .audit.routing.os_release import os_release_path
from .audit.yaml_io import suggestion_files
from .core import (
    Annotation,
    Category,
    ProcessInfo,
    provider_of,
    section_for,
    section_reason,
)
from .core.tree.process_tree import ProcessTree
from .process.cache import shown_path
from .process.heuristics import ATTENTION_PATH, HEURISTICS_PATH
from .process.verify import VerificationCache, inspect_executable

PACKAGE = Path(__file__).parent


def snapshot_payload(
    store: AuditStore,
    processes: tuple[ProcessInfo, ...],
) -> list[dict[str, Any]]:
    tree = ProcessTree(processes)
    return [
        _snapshot_process(
            store,
            process,
            tree.parent_annotation(process, store.annotations),
            typed=tree.typed(process, store.annotations),
            agent_shell=tree.agent_shell(process, store.annotations),
            vouched=tree.vouched(process, store.annotations),
        )
        for process in processes
    ]


def _snapshot_process(
    store: AuditStore,
    process: ProcessInfo,
    parent: Annotation | None,
    *,
    typed: bool,
    agent_shell: bool,
    vouched: bool,
) -> dict[str, Any]:
    annotation = store.annotation_for(process.signature)
    return {
        "pid": process.pid,
        "ppid": process.ppid,
        "name": process.name,
        "user": process.user,
        "state": process.state,
        "exe": process.exe,
        "command": process.command,
        "signature": process.signature,
        "trust": annotation.category.value if annotation else None,
        "provider": provider_of(process, annotation),
        "covered_by_parent": annotation is None
        and parent is not None
        and parent.covers(process.name),
        **(annotation.flags() if annotation else {}),
        "source": store.source_for(process.signature),
        "suggested": _suggested(store, process.signature, annotation),
        "section": section_for(
            process,
            annotation,
            parent,
            typed=typed,
            agent_shell=agent_shell,
            vouched=vouched,
        ).value,
        "weird": section_reason(
            process, annotation, parent, typed=typed, vouched=vouched
        ),
        "typed_in_terminal": typed,
        "agent_shell": agent_shell,
        "service": process.service,
        "listens": list(process.listens),
        "exposed": process.exposed,
    }


def rules_payload(store: AuditStore) -> list[dict[str, Any]]:
    return [
        {
            "signature": row.signature,
            "trust": row.category.value,
            "provider": store.annotations[row.signature].provider,
            "note": row.note,
            "source": row.source,
            "changed": row.changed,
            "children": store.annotations[row.signature].children,
            **store.annotations[row.signature].flags(),
        }
        for row in store.rule_rows()
    ]


def annotate_session(
    store: AuditStore,
    signature: str,
    trust: str,
    note: str | None = None,
    children: tuple[str, ...] | None = None,
    flags: dict[str, bool] | None = None,
    agents: tuple[str, ...] | None = None,
    plugin_args: tuple[str, ...] | None = None,
    provider: str | None = None,
) -> Annotation:
    return store.set(
        signature,
        Category(trust),
        note=note,
        provider=provider,
        children=children,
        flags=flags,
        agents=agents,
        plugin_args=plugin_args,
    )


def verify_payload(
    path: str,
    cache: VerificationCache | None = None,
) -> dict[str, Any]:
    return asdict(inspect_executable(path, cache))


def _suggested(
    store: AuditStore, signature: str, annotation: Annotation | None
) -> dict[str, str] | None:
    suggestion = store.suggestions.get(signature)
    if suggestion is None or annotation is not None:
        return None
    return {"trust": suggestion.category.value, "note": suggestion.note}


def paths_payload(store: AuditStore, cache_dir: Path | None) -> list[dict[str, Any]]:
    """Every place the tool reads or writes, and whether the user can write
    it: whatever the user can write, any process running as them can too."""
    places = [
        ("code", PACKAGE, "the program that runs"),
        ("base audit", store.root, f"scopes read: {_scopes_read(store)}"),
        (
            "suggestions",
            store.root,
            f"{len(suggestion_files(store.root, store.scopes))} file(s), never trusted",
        ),
        ("heuristics", HEURISTICS_PATH, "what looks weird"),
        ("attention", ATTENTION_PATH, "argument-bound programs, doors to root"),
        ("families", FAMILIES_PATH, "family routing"),
        ("os-release", os_release_path(), "names the distribution"),
    ]
    if store.session_path is not None:
        places.append(("your layer", store.session_path, "your annotations"))
        places.append((
            "journal",
            store.session_path.with_name(HISTORY_FILENAME),
            "every change to your layer",
        ))
    if cache_dir is not None:
        places.append(("cache", cache_dir / "verification.json", "disposable"))
    overrides = sorted(name for name in os.environ if name.startswith("TOP_ANNOTATOR_"))
    return [
        {
            "what": what,
            "path": str(path),
            "exists": path.exists(),
            "writable_by_you": _writable(path),
            "note": note,
            "overrides": overrides,
        }
        for what, path, note in places
    ]


def paths_text(places: list[dict[str, Any]]) -> str:
    lines = [
        f"{place['what']:<12} {_access(place):<10} {shown_path(Path(place['path']))}"
        f"  ({place['note']})"
        for place in places
    ]
    overrides = places[0]["overrides"] if places else []
    if overrides:
        lines.append(f"overridden by: {', '.join(overrides)}")
    return "\n".join(lines)


def _access(place: dict[str, Any]) -> str:
    if not place["exists"]:
        return "missing"
    return "yours" if place["writable_by_you"] else "read-only"


def _writable(path: Path) -> bool:
    existing = next(
        (candidate for candidate in (path, *path.parents) if candidate.exists()), path
    )
    return os.access(existing, os.W_OK)


def _scopes_read(store: AuditStore) -> str:
    read = [scope for scope in store.scopes if (store.root / scope).is_dir()]
    return ", ".join(read) or "the whole folder"


def emit(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
