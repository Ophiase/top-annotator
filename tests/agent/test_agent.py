from top_annotator.agent import annotate_session, rules_payload, snapshot_payload
from top_annotator.audit import AuditStore
from top_annotator.core.category import Category

from ..factories import process


def test_snapshot_exposes_trust_and_section(tmp_path) -> None:
    store = AuditStore.load(tmp_path / "audit.yaml")
    store.set("myapp|/usr/bin/myapp", Category.TRUST)
    payload = snapshot_payload(
        store,
        (
            process(
                7,
                1,
                name="myapp",
                exe="/usr/bin/myapp",
                signature="myapp|/usr/bin/myapp",
            ),
        ),
    )

    assert payload[0]["trust"] == "trust"
    assert payload[0]["section"] == "SAFE"


def test_rules_payload_distinguishes_session_and_audit(tmp_path) -> None:
    audit = tmp_path / "audit.yaml"
    audit.write_text(
        "version: 1\nannotations:\n  audit|/usr/bin/audit: safe\n",
        encoding="utf-8",
    )
    session = tmp_path / "cache" / "session.yaml"
    store = AuditStore.load(audit, session_path=session)
    annotate_session(store, "session|/usr/bin/session", "core", "live")

    sources = {
        row["source"]
        for row in rules_payload(store)
        if row["signature"].startswith(("audit|", "session|"))
    }

    assert sources == {"session", "audit.yaml"}


def test_annotate_without_note_keeps_the_note(tmp_path) -> None:
    store = AuditStore.load(tmp_path / "audit", session_path=tmp_path / "s.yaml")
    annotate_session(store, "tool|/usr/bin/tool", "safe", "why it is fine")
    kept = annotate_session(store, "tool|/usr/bin/tool", "safe", children=("sh",))
    assert kept.note == "why it is fine"
    assert kept.children == ("sh",)


def test_snapshot_marks_a_child_covered_by_its_parent(tmp_path) -> None:
    store = AuditStore.load(tmp_path / "audit", session_path=tmp_path / "s.yaml")
    annotate_session(store, "term|/usr/bin/term", "trust", children=("zsh",))
    processes = (
        process(1, name="term", exe="/usr/bin/term", signature="term|/usr/bin/term"),
        process(2, 1, name="zsh", exe="/usr/bin/zsh"),
    )
    shell = snapshot_payload(store, processes)[1]
    assert shell["covered_by_parent"] is True
    assert shell["section"] == "SAFE"


def test_snapshot_marks_the_shells_of_an_agent(tmp_path) -> None:
    store = AuditStore.load(tmp_path / "audit", session_path=tmp_path / "s.yaml")
    annotate_session(store, "host|/usr/bin/host", "safe", agents=("claude",))
    processes = (
        process(1, name="host", exe="/usr/bin/host", signature="host|/usr/bin/host"),
        process(2, 1, name="claude", exe="/opt/claude/2.1/claude"),
        process(3, 2, name="zsh", exe="/usr/bin/zsh"),
        process(4, 3, name="make", exe="/usr/bin/make"),
    )
    payload = snapshot_payload(store, processes)
    assert [entry["section"] for entry in payload] == ["SAFE", "SAFE", "SAFE", "NEW"]
    assert payload[2]["agent_shell"] is True
