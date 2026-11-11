from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from . import __version__
from .agent import (
    annotate_session,
    emit,
    rules_payload,
    snapshot_payload,
    verify_payload,
)
from .audit import BASE_VARIABLE, AuditStore, default_audit_path
from .core.annotation import FLAGS
from .core.category import PROVIDERS, Category
from .process.cache import (
    DATA_VARIABLE,
    default_cache_dir,
    default_data_dir,
    shown_path,
)
from .process.scan import ProcessScanner, Scanner
from .process.scan.demo import DEMO_NOTICE, DemoMachine
from .process.verify import VerificationCache
from .tui import TopAnnotatorApp

SESSION_FILENAME = "session.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="top-annotator",
        description="A tiny btop-like process viewer focused on audit status.",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=None,
        help=(
            f"base audit folder or YAML file (default: ${BASE_VARIABLE}, else the"
            " audit bundled with the tool); your own annotations go to"
            f" ${DATA_VARIABLE}/session.yaml"
            f" (now: {shown_path(default_data_dir() / SESSION_FILENAME)})"
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="refresh interval (default: 2.0)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="run on a bundled fictional machine; changes are discarded on exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("snapshot", help="print every process with trust and section")
    commands.add_parser("rules", help="print the effective audit and session rules")
    annotate = commands.add_parser("annotate", help="write a session annotation")
    annotate.add_argument("signature")
    annotate.add_argument("trust", choices=[category.value for category in Category])
    annotate.add_argument("--note", default=None)
    annotate.add_argument(
        "--provider",
        choices=list(PROVIDERS),
        default=None,
        help="who ships it: " + ", ".join(PROVIDERS),
    )
    annotate.add_argument(
        "--children",
        metavar="NAMES",
        help="comma-separated child names this process vouches for",
    )
    annotate.add_argument(
        "--agents",
        metavar="NAMES",
        help="comma-separated child names that are AI agents",
    )
    annotate.add_argument(
        "--plugin-args",
        metavar="ARGS",
        help="comma-separated argv markers of its plugin hosts; their shells are not "
        "terminal shells",
    )
    for flag, meaning in FLAGS.items():
        annotate.add_argument(
            f"--{flag}",
            action="store_true",
            default=None,
            help=meaning,
        )
    commands.add_parser("undo", help="revert the latest change to your session")
    verify = commands.add_parser("verify", help="check package origin and dpkg -V")
    verify.add_argument("path")
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    if arguments.demo:
        with tempfile.TemporaryDirectory(prefix="top-annotator-demo-") as scratch:
            machine = DemoMachine(Path(scratch))
            _dispatch(arguments, machine.store(), machine.scanner(), None, DEMO_NOTICE)
        return
    cache_dir = default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    audit_path = arguments.cache or default_audit_path()
    store = AuditStore.load(
        audit_path.expanduser().resolve(),
        session_path=default_data_dir() / SESSION_FILENAME,
    )
    _dispatch(arguments, store, ProcessScanner(), cache_dir, "")


def _dispatch(
    arguments: argparse.Namespace,
    store: AuditStore,
    scanner: Scanner,
    cache_dir: Path | None,
    notice: str,
) -> None:
    if arguments.command == "snapshot":
        emit(snapshot_payload(store, scanner.scan()))
    elif arguments.command == "rules":
        emit(rules_payload(store))
    elif arguments.command == "annotate":
        _annotate(arguments, store)
    elif arguments.command == "undo":
        _undo(store)
    elif arguments.command == "verify":
        cache = VerificationCache(cache_dir) if cache_dir is not None else None
        emit(verify_payload(arguments.path, cache))
    else:
        TopAnnotatorApp(
            store,
            scanner=scanner,
            refresh_seconds=arguments.interval,
            cache_dir=cache_dir,
            notice=notice,
        ).run()


def _annotate(arguments: argparse.Namespace, store: AuditStore) -> None:
    annotation = annotate_session(
        store,
        arguments.signature,
        arguments.trust,
        arguments.note,
        _children(arguments.children),
        {flag: True for flag in FLAGS if getattr(arguments, flag) is not None},
        _children(arguments.agents),
        _children(arguments.plugin_args),
        arguments.provider,
    )
    emit({
        "signature": arguments.signature,
        "trust": annotation.category.value,
        "provider": annotation.provider,
        "note": annotation.note,
        "children": annotation.children,
        **annotation.flags(),
        "agents": annotation.agents,
        "written_to": str(store.session_path),
    })


def _undo(store: AuditStore) -> None:
    signature = store.undo()
    annotation = store.annotation_for(signature) if signature else None
    emit({
        "undone": signature,
        "trust": annotation.category.value if annotation else None,
    })


def _children(raw: str | None) -> tuple[str, ...] | None:
    if raw is None:
        return None
    return tuple(name.strip() for name in raw.split(",") if name.strip())


if __name__ == "__main__":
    main()
