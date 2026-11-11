from __future__ import annotations

from top_annotator.core import Annotation, Category, Section, section_for
from top_annotator.core.section import section_reason, typed_in_terminal

from ..factories import process

SAFE = Annotation(category=Category.SAFE)
NO_CHILDREN = Annotation(category=Category.SAFE, children=(), exclusive=True)
NGINX = Annotation(
    category=Category.SAFE,
    children=("nginx",),
    exclusive=True,
)
TERMINAL = Annotation(category=Category.TRUST, children=("zsh",))


def test_service_comes_from_a_service_unit() -> None:
    assert process(1, unit="ollama.service").service == "ollama"
    assert process(2, unit="app-kitty-1.scope").service == ""


def test_loopback_only_is_not_exposed() -> None:
    assert not process(1, listens=("tcp 127.0.0.1:8384", "tcp [::1]:631")).exposed
    assert process(2, listens=("tcp 127.0.0.1:8384", "tcp 0.0.0.0:445")).exposed


def test_child_without_declaration_is_judged_alone() -> None:
    child = process(2, 1, name="anything")
    assert section_for(child, SAFE, SAFE) is Section.SAFE


def test_expected_child_stays_safe() -> None:
    child = process(2, 1, name="nginx")
    assert section_for(child, SAFE, NGINX) is Section.SAFE


def test_unexpected_child_goes_weird_even_when_safe() -> None:
    child = process(2, 1, name="sh")
    assert section_for(child, SAFE, NGINX) is Section.WEIRD
    assert "expected: nginx" in section_reason(child, SAFE, NGINX)


def test_empty_declaration_allows_no_child() -> None:
    child = process(2, 1, name="bash")
    assert section_for(child, None, NO_CHILDREN) is Section.WEIRD
    assert "expected: none" in section_reason(child, None, NO_CHILDREN)


def test_personal_is_reviewed() -> None:
    mine = Annotation(category=Category.PERSONAL)
    assert section_for(process(1), mine) is Section.SAFE


def test_covered_child_is_reviewed_through_its_parent() -> None:
    shell = process(3, 2, name="zsh")
    assert section_for(shell, None, TERMINAL) is Section.SAFE


def test_grandchild_is_not_covered() -> None:
    command = process(4, 3, name="make")
    assert section_for(command, None, None) is Section.NEW


def test_non_exclusive_parent_leaves_other_children_new() -> None:
    other = process(5, 2, name="htop")
    assert section_for(other, None, TERMINAL) is Section.NEW


KITTY = Annotation(category=Category.TRUST, terminal=True)
HTOP = Annotation(category=Category.TRUST, interactive=True)


def test_terminal_covers_its_shells_only() -> None:
    assert KITTY.covers("zsh")
    assert not KITTY.covers("htop")


def test_typed_needs_a_shell_under_a_terminal() -> None:
    shell = process(3, 2, name="zsh")
    assert typed_in_terminal(shell, KITTY)
    assert not typed_in_terminal(shell, SAFE)
    assert not typed_in_terminal(process(4, 2, name="python3"), KITTY)


def test_interactive_program_is_safe_when_typed() -> None:
    htop = process(5, 3, name="htop")
    assert section_for(htop, HTOP, None, typed=True) is Section.SAFE


def test_interactive_program_started_elsewhere_goes_weird() -> None:
    htop = process(5, 3, name="htop")
    assert section_for(htop, HTOP, None, typed=False) is Section.WEIRD
    assert "user terminal" in section_reason(htop, HTOP, None, typed=False)


def test_agent_shell_is_reviewed_but_not_what_it_runs() -> None:
    shell = process(6, 5, name="zsh")
    assert section_for(shell, None, None, agent_shell=True) is Section.SAFE
    assert section_for(process(7, 6, name="make"), None, None) is Section.NEW


def test_agents_list_covers_the_named_child() -> None:
    host = Annotation(category=Category.SAFE, agents=("claude",))
    assert host.covers("claude")
    assert not host.covers("node")
