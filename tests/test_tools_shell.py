import sys
from pathlib import Path

import pytest

from ai_code_agent.tools.shell import run_command, run_python_file


def test_run_command_echo(tmp_path: Path):
    out = run_command(tmp_path, "echo hello")
    assert "hello" in out
    assert "[exit 0]" in out


def test_run_command_nonzero_exit(tmp_path: Path):
    out = run_command(tmp_path, "exit 3")
    assert "[exit 3]" in out


def test_run_command_timeout(tmp_path: Path):
    out = run_command(tmp_path, f"{sys.executable} -c 'import time; time.sleep(2)'", timeout=1)
    assert "timeout" in out.lower()


def test_run_command_empty_rejected(tmp_path: Path):
    with pytest.raises(ValueError):
        run_command(tmp_path, "   ")


def test_run_python_file(tmp_path: Path):
    script = tmp_path / "hi.py"
    script.write_text("print('alive')\n")
    out = run_python_file(tmp_path, "hi.py")
    assert "alive" in out
    assert "[exit 0]" in out


def test_run_python_file_with_args(tmp_path: Path):
    script = tmp_path / "args.py"
    script.write_text("import sys; print('ARGS:', ' '.join(sys.argv[1:]))\n")
    out = run_python_file(tmp_path, "args.py", args=["one", "two"])
    assert "ARGS: one two" in out


def test_run_python_file_rejects_non_py(tmp_path: Path):
    (tmp_path / "x.sh").write_text("echo hi")
    with pytest.raises(ValueError):
        run_python_file(tmp_path, "x.sh")


def test_run_python_file_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        run_python_file(tmp_path, "nope.py")
