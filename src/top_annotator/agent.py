from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from .audit import AuditStore
from .core import (
    Annotation,
    Category,
    ProcessInfo,
    provider_of,
    section_for,
    section_reason,
)
from .core.tree.process_tree import ProcessTree
from .process.verify import VerificationCache, inspect_executable


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


def emit(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
