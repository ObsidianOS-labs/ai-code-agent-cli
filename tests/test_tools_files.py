from pathlib import Path

import pytest

from ai_code_agent.safety import PathEscapeError
from ai_code_agent.tools.files import (
    get_file_content,
    get_files_info,
    write_file,
)


def test_get_files_info_lists_entries(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "subdir").mkdir()
    listing = get_files_info(tmp_path, ".")
    assert "a.txt" in listing
    assert "subdir" in listing
    assert "file" in listing
    assert "dir" in listing


def test_get_files_info_empty_dir(tmp_path: Path):
    sub = tmp_path / "empty"
    sub.mkdir()
    listing = get_files_info(tmp_path, "empty")
    assert "(empty)" in listing


def test_get_files_info_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        get_files_info(tmp_path, "nope")


def test_get_files_info_traversal_blocked(tmp_path: Path):
    inner = tmp_path / "inner"
    inner.mkdir()
    with pytest.raises(PathEscapeError):
        get_files_info(inner, "../")


def test_get_file_content_reads_file(tmp_path: Path):
    (tmp_path / "x.txt").write_text("payload-123")
    assert get_file_content(tmp_path, "x.txt") == "payload-123"


def test_get_file_content_truncates(tmp_path: Path):
    (tmp_path / "big.txt").write_text("a" * 1000)
    out = get_file_content(tmp_path, "big.txt", max_bytes=10)
    assert out.startswith("a" * 10)
    assert "[truncated" in out


def test_get_file_content_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        get_file_content(tmp_path, "missing.txt")


def test_get_file_content_directory_errors(tmp_path: Path):
    (tmp_path / "d").mkdir()
    with pytest.raises(IsADirectoryError):
        get_file_content(tmp_path, "d")


def test_write_file_creates_and_overwrites(tmp_path: Path):
    msg = write_file(tmp_path, "nested/dir/note.md", "# hi")
    assert "Wrote" in msg
    assert (tmp_path / "nested/dir/note.md").read_text() == "# hi"

    write_file(tmp_path, "nested/dir/note.md", "second")
    assert (tmp_path / "nested/dir/note.md").read_text() == "second"


def test_write_file_blocks_directory(tmp_path: Path):
    (tmp_path / "d").mkdir()
    with pytest.raises(IsADirectoryError):
        write_file(tmp_path, "d", "no")


def test_write_file_blocks_traversal(tmp_path: Path):
    inner = tmp_path / "inner"
    inner.mkdir()
    with pytest.raises(PathEscapeError):
        write_file(inner, "../outside.txt", "no")
