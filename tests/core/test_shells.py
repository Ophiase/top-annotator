from __future__ import annotations

from top_annotator.core.annotation import Annotation
from top_annotator.core.category import Category
from top_annotator.core.section import Section, section_for
from top_annotator.core.tree import ProcessTree

from ..factories import process

EDITOR = "code|/usr/share/code/code"
PLUGIN_ARG = "--inspect-port=0"
EDITOR_ENTRY = Annotation(
    category=Category.HOST,
    terminal=True,
    agents=("claude",),
    plugin_args=(PLUGIN_ARG,),
)
INIT = process(1, 0, name="systemd", signature="systemd")
PTY_HOST = process(
    10, 1, name="code", cmdline=("code", "--type=utility"), signature=EDITOR
)
PLUGINS = process(11, 1, name="code", cmdline=("code", PLUGIN_ARG), signature=EDITOR)
TERMINAL_SHELL = process(20, 10, name="zsh", signature="zsh")
TYPED_TOOL = process(21, 20, name="just", signature="just")
RECIPE_SHELL = process(22, 21, name="sh", signature="sh")
PLUGIN_SHELL = process(30, 11, name="zsh", signature="zsh")
AGENT = process(31, 11, name="claude", signature="claude")
AGENT_SHELL = process(32, 31, name="zsh", signature="zsh")
AGENT_TOOL = process(33, 32, name="just", signature="just")
AGENT_RECIPE_SHELL = process(34, 33, name="sh", signature="sh")
DAEMON_SHELL = process(40, 1, name="bash", signature="bash")
DAEMON_TOOL = process(41, 1, name="cron", signature="cron")
DAEMON_TOOL_SHELL = process(42, 41, name="sh", signature="sh")
PROCESSES = (
    AGENT_TOOL,
    AGENT_RECIPE_SHELL,
    DAEMON_TOOL,
    DAEMON_TOOL_SHELL,
    INIT,
    PTY_HOST,
    PLUGINS,
    TERMINAL_SHELL,
    TYPED_TOOL,
    RECIPE_SHELL,
    PLUGIN_SHELL,
    AGENT,
    AGENT_SHELL,
    DAEMON_SHELL,
)


def section(target: object) -> Section:
    tree = ProcessTree(PROCESSES)
    annotations = {EDITOR: EDITOR_ENTRY}
    assert target in PROCESSES
    found = next(item for item in PROCESSES if item is target)
    return section_for(
        found,
        annotations.get(found.signature),
        tree.parent_annotation(found, annotations),
        typed=tree.typed(found, annotations),
        agent_shell=tree.agent_shell(found, annotations),
        vouched=tree.vouched(found, annotations),
    )


def test_a_terminal_shell_is_safe() -> None:
    assert section(TERMINAL_SHELL) is Section.SAFE


def test_a_shell_from_a_command_the_user_typed_is_not_weird() -> None:
    assert section(RECIPE_SHELL) is Section.NEW


def test_an_agent_shell_is_safe() -> None:
    assert section(AGENT_SHELL) is Section.SAFE


def test_a_shell_spawned_by_a_plugin_host_is_weird() -> None:
    assert section(PLUGIN_SHELL) is Section.WEIRD


def test_a_shell_nothing_accounts_for_is_weird() -> None:
    assert section(DAEMON_SHELL) is Section.WEIRD


def test_a_host_itself_sits_in_safe() -> None:
    assert section(PLUGINS) is Section.SAFE


def test_a_shell_from_a_command_an_agent_ran_is_not_weird() -> None:
    assert section(AGENT_RECIPE_SHELL) is Section.NEW


def test_a_shell_from_a_tool_no_shell_started_is_weird() -> None:
    assert section(DAEMON_TOOL_SHELL) is Section.WEIRD
