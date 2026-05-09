from pathlib import Path

import pytest

from ai_code_agent.safety import PathEscapeError, relative_display, resolve_within


def test_resolve_within_relative(tmp_path: Path):
    target = tmp_path / "sub" / "file.txt"
    target.parent.mkdir(parents=True)
    target.write_text("x")
    resolved = resolve_within(tmp_path, "sub/file.txt")
    assert resolved == target.resolve()


def test_resolve_within_dot(tmp_path: Path):
    assert resolve_within(tmp_path, ".") == tmp_path.resolve()


def test_resolve_within_blocks_parent_traversal(tmp_path: Path):
    inner = tmp_path / "inner"
    inner.mkdir()
    with pytest.raises(PathEscapeError):
        resolve_within(inner, "../escape")


def test_resolve_within_blocks_absolute_outside(tmp_path: Path):
    with pytest.raises(PathEscapeError):
        resolve_within(tmp_path, "/etc/passwd")


def test_relative_display(tmp_path: Path):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert relative_display(tmp_path, sub) == "a/b"
    assert relative_display(tmp_path, tmp_path) == "."
