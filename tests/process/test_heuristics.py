from dataclasses import replace

from top_annotator.process.heuristics import (
    HEURISTICS_PATH,
    HeuristicsConfig,
    is_kernel_thread,
    weird_reason,
)

from ..factories import process


def test_heuristics_are_loaded_from_yaml() -> None:
    config = HeuristicsConfig.load(HEURISTICS_PATH)

    assert "/usr/libexec/" in config.system_directories
    assert "systemd" in config.system_executables
    assert config.name_aliases["systemd"] == frozenset({"init", "systemd"})
    assert config.kernel_thread_parent_pids == frozenset({0, 2})


def test_kernel_thread_has_no_executable_and_no_argv() -> None:
    thread = process(42, 2, name="kworker/0:1H", exe="", cmdline=())

    assert is_kernel_thread(thread)


def test_kthreadd_itself_is_a_kernel_thread() -> None:
    assert is_kernel_thread(process(2, 0, name="kthreadd", exe="", cmdline=()))


def test_a_child_of_kthreadd_with_an_executable_is_not_a_kernel_thread() -> None:
    child = process(42, 2, name="helper", exe="/usr/bin/helper")

    assert not is_kernel_thread(child)


def test_system_name_running_from_tmp_is_weird() -> None:
    fake = process(42, 1, name="systemd", exe="/tmp/systemd")

    assert weird_reason(fake) == "executable runs from tmp/"


def test_system_name_with_the_wrong_executable_is_weird() -> None:
    fake = process(42, 1, name="gsd-color", exe="/usr/bin/python3")

    assert "executable is 'python3'" in (weird_reason(fake) or "")


def test_truncated_system_name_is_not_weird() -> None:
    legit = process(
        42,
        1,
        name="gnome-session-b",
        exe="/usr/libexec/gnome-session-binary",
    )

    assert weird_reason(legit) is None


def test_systemd_init_alias_is_not_weird() -> None:
    legit = process(1, 0, name="systemd", exe="", cmdline=("/sbin/init",))

    assert weird_reason(legit) is None


def test_zombie_is_weird() -> None:
    zombie = process(42, 1, name="sd_espeak-ng-mb", exe="", cmdline=())
    zombie = replace(zombie, state="Z")

    assert weird_reason(zombie) == "zombie: exited but not reaped by its parent"


def test_deleted_executable_is_weird() -> None:
    deleted = process(42, 1, name="tool", exe="/usr/bin/tool (deleted)")

    assert weird_reason(deleted) == "executable was deleted"
