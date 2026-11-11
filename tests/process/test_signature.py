from pathlib import Path

from top_annotator.process.signature import process_signature


def test_python_script_is_part_of_the_signature() -> None:
    signature = process_signature(
        "python3",
        "/usr/bin/python3",
        ("/usr/bin/python3", "/home/me/tool.py", "--flag"),
    )

    assert signature == "python3|/usr/bin/python3|/home/me/tool.py"


def test_plain_binary_uses_name_and_executable() -> None:
    signature = process_signature(
        "gsd-xsettings",
        "/usr/libexec/gsd-xsettings",
        ("/usr/libexec/gsd-xsettings",),
    )

    assert signature == "gsd-xsettings|/usr/libexec/gsd-xsettings"


def test_root_process_falls_back_to_argv_zero() -> None:
    signature = process_signature("systemd", "", ("/sbin/init", "splash"))

    assert signature == "systemd|/sbin/init"


def test_kernel_thread_falls_back_to_its_name() -> None:
    assert process_signature("kthreadd", "", ()) == "kthreadd|kthreadd"


def test_deleted_executable_is_normalized(tmp_path: Path) -> None:
    executable = str(tmp_path / "tool")
    signature = process_signature("tool", f"{executable} (deleted)", (executable,))

    assert signature == f"tool|{executable}"


def test_inline_shell_command_keeps_only_its_first_word() -> None:
    command = "source /home/me/.claude/shell-snapshots/snap.sh && eval 'ls -la'"
    signature = process_signature(
        "zsh", "/usr/bin/zsh", ("/usr/bin/zsh", "-c", command)
    )

    assert signature == "zsh|/usr/bin/zsh|-c source"


def test_inline_launcher_keeps_the_program_it_starts() -> None:
    signature = process_signature("sh", "/usr/bin/dash", ("/bin/sh", "-c", "alacritty"))

    assert signature == "sh|/usr/bin/dash|-c alacritty"


def test_inline_python_without_code_is_just_dash_c() -> None:
    signature = process_signature("python3", "/usr/bin/python3", ("python3", "-c"))

    assert signature == "python3|/usr/bin/python3|-c"
