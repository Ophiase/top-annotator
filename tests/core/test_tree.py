from __future__ import annotations

from dataclasses import replace

from top_annotator.core.annotation import Annotation
from top_annotator.core.category import Category
from top_annotator.core.section import Section, section_for
from top_annotator.core.section_header import SectionHeader
from top_annotator.core.tree import ProcessRow, ProcessTree
from top_annotator.core.tree.process_row import TREE_SCOPE, fold_key

from ..factories import process

ROOT = process(1, 0, name="systemd")
MIDDLE = process(2, 1, name="gnome-session")
LEAF = process(3, 2, name="gsd-xsettings")
OTHER = process(4, 0, name="alacritty")
PROCESSES = (ROOT, MIDDLE, LEAF, OTHER)


def tree() -> ProcessTree:
    return ProcessTree(PROCESSES)


def test_tree_rows_are_depth_first() -> None:
    rows = tree().rows(annotations={})

    assert [row.process.pid for row in rows] == [1, 2, 3, 4]
    assert [row.depth for row in rows] == [0, 1, 2, 0]
    assert rows[2].prefix.startswith("│     └─")


def test_search_keeps_the_parent_chain() -> None:
    rows = tree().rows(annotations={}, query="gsd")

    assert [row.process.pid for row in rows] == [1, 2, 3]


def test_only_unannotated_keeps_parent_context() -> None:
    annotations = {LEAF.signature: Annotation(Category.SAFE)}

    rows = tree().rows(annotations=annotations, view_filter="unreviewed")

    assert [row.process.pid for row in rows] == [1, 2, 4]


def test_folding_hides_descendants() -> None:
    rows = tree().rows(annotations={}, folded=frozenset({fold_key(TREE_SCOPE, 2)}))

    assert [row.process.pid for row in rows] == [1, 2, 4]
    assert rows[1].folded


def test_parent_chain_goes_root_first() -> None:
    chain = tree().parent_chain(LEAF)

    assert [item.pid for item in chain] == [1, 2, 3]


def test_new_section_duplicates_safe_ancestors_as_context() -> None:
    safe_parent = process(
        10,
        0,
        name="gnome-session-b",
        exe="/usr/libexec/gnome-session-binary",
    )
    new_child = process(11, 10, name="myapp", exe="/usr/bin/myapp")
    tree = ProcessTree((safe_parent, new_child))
    rows = tree.section_rows(
        annotations={safe_parent.signature: Annotation(Category.SAFE)}
    )
    new_rows = [
        row
        for row in rows
        if isinstance(row, ProcessRow) and row.process.pid in {10, 11}
    ]

    assert [row.process.pid for row in new_rows] == [10, 11, 10]
    assert new_rows[0].is_context
    assert not new_rows[1].is_context
    assert not new_rows[2].is_context


def test_kernel_threads_sit_last_by_family_and_start_folded() -> None:
    kernel = process(2, 0, name="kthreadd", exe="", cmdline=())
    worker = process(3, 2, name="kworker/0:1", exe="", cmdline=())
    journal = process(4, 2, name="jbd2/nvme0n1p2-8", exe="", cmdline=())
    safe = process(10, 0, name="gsd-color", exe="/usr/libexec/gsd-color")
    tree = ProcessTree((kernel, worker, journal, safe))
    annotations = {safe.signature: Annotation(Category.SAFE, provider="desktop")}

    rows = tree.section_rows(
        annotations=annotations,
        folded=tree.default_folded() - {"SAFE/kernel"},
    )
    labels = [
        row.group if isinstance(row, SectionHeader) else row.process.name
        for row in rows
    ]

    assert labels == [
        "",
        "desktop",
        "gsd-color",
        "kernel",
        "kthreadd",
        "kernel/kworker",
        "kernel/storage",
    ]
    assert all(
        row.folded
        for row in rows
        if isinstance(row, SectionHeader) and "/" in row.group
    )


def test_sections_are_ordered_weird_new_safe() -> None:
    safe = process(
        10,
        0,
        name="gsd-color",
        exe="/usr/libexec/gsd-color",
    )
    weird = process(11, 0, name="systemd", exe="/tmp/systemd")
    new = process(12, 0, name="myapp", exe="/usr/bin/myapp")
    rows = ProcessTree((safe, weird, new)).section_rows(
        annotations={safe.signature: Annotation(Category.SAFE)}
    )
    headers = [row for row in rows if isinstance(row, SectionHeader) and not row.group]

    assert [header.section for header in headers] == [
        Section.WEIRD,
        Section.NEW,
        Section.SAFE,
    ]


def test_a_fold_in_one_band_leaves_the_same_process_open_in_another() -> None:
    parent = process(1, 0, name="systemd", exe="/sbin/init")
    safe_child = process(2, 1, name="dbus", exe="/usr/bin/dbus")
    new_child = process(3, 1, name="myapp", exe="/usr/bin/myapp")
    annotations = {
        parent.signature: Annotation(Category.CORE, provider="systemd"),
        safe_child.signature: Annotation(Category.SAFE, provider="systemd"),
    }
    rows = ProcessTree((parent, safe_child, new_child)).section_rows(
        annotations=annotations,
        folded=frozenset({fold_key("NEW", 1)}),
    )
    folded = {row.key: row.folded for row in rows if isinstance(row, ProcessRow)}

    assert folded[fold_key("NEW", 1)]
    assert not folded[fold_key("SAFE/systemd", 1)]


def test_safe_band_is_split_by_provider_with_kernel_last() -> None:
    kernel = process(2, 0, name="kthreadd", exe="", cmdline=())
    init = process(1, 0, name="systemd", exe="/sbin/init")
    session = process(5, 1, name="gnome-shell", exe="/usr/bin/gnome-shell")
    shell = process(6, 5, name="zsh", exe="/usr/bin/zsh")
    mine = process(7, 1, name="tool", exe="/usr/bin/tool")
    annotations = {
        init.signature: Annotation(Category.CORE, provider="systemd"),
        session.signature: Annotation(Category.SAFE, provider="desktop", terminal=True),
        mine.signature: Annotation(Category.TRUST),
    }
    rows = ProcessTree((kernel, init, session, shell, mine)).section_rows(
        annotations=annotations
    )
    groups = {
        row.group: row.count
        for row in rows
        if isinstance(row, SectionHeader) and row.group
    }

    assert list(groups) == ["unlabelled", "desktop", "systemd", "kernel"]
    assert groups["desktop"] == 2


def test_safe_groups_start_folded() -> None:
    init = process(1, 0, name="systemd", exe="/sbin/init")
    tree = ProcessTree((init,))
    rows = tree.section_rows(
        annotations={init.signature: Annotation(Category.CORE, provider="systemd")},
        folded=tree.default_folded(),
    )

    assert [type(row).__name__ for row in rows] == ["SectionHeader"] * 2
    assert isinstance(rows[1], SectionHeader)
    assert rows[1].folded


def test_a_group_header_names_its_shared_ancestors_and_keeps_the_tree() -> None:
    init = process(1, 0, name="systemd", exe="/sbin/init")
    user = process(3, 1, name="systemd", exe="/usr/lib/systemd/systemd")
    shell = process(5, 3, name="gnome-shell", exe="/usr/bin/gnome-shell")
    firefox = process(9, 5, name="firefox", exe="/usr/bin/firefox")
    editor = process(11, 3, name="code", exe="/usr/bin/code")
    annotations = {
        init.signature: Annotation(Category.CORE, provider="systemd"),
        user.signature: Annotation(Category.CORE, provider="systemd"),
        shell.signature: Annotation(Category.SAFE, provider="desktop"),
        firefox.signature: Annotation(Category.TRUST, provider="app"),
        editor.signature: Annotation(Category.TRUST, provider="app"),
    }
    rows = ProcessTree((init, user, shell, firefox, editor)).section_rows(
        annotations=annotations
    )
    app = next(
        index
        for index, row in enumerate(rows)
        if isinstance(row, SectionHeader) and row.group == "app"
    )
    header = rows[app]
    assert isinstance(header, SectionHeader)
    below = [
        (row.process.name, row.is_context)
        for row in rows[app + 1 : app + 4]
        if isinstance(row, ProcessRow)
    ]

    assert header.parents == ("systemd", "systemd")
    assert below == [("gnome-shell", True), ("firefox", False), ("code", False)]


def test_an_identified_zombie_leaves_weird() -> None:
    zombie = process(7, 1, name="zypak-sandbox", exe="", signature="zypak|zypak")
    zombie = replace(zombie, state="Z")
    unknown = section_for(zombie, None)
    known = section_for(zombie, Annotation(Category.TRUST, provider="app"))
    watched = section_for(zombie, Annotation(Category.WATCH))

    assert (unknown, known, watched) == (Section.WEIRD, Section.SAFE, Section.WEIRD)
