from pathlib import Path

import pytest

from ai_code_agent.tools.search import grep_search


def test_grep_search_finds_matches(tmp_path: Path):
    (tmp_path / "a.py").write_text("def foo():\n    return 1\n")
    (tmp_path / "b.py").write_text("def bar():\n    return foo()\n")
    out = grep_search(tmp_path, r"\bfoo\b")
    assert "a.py:1" in out
    assert "b.py:2" in out


def test_grep_search_no_matches(tmp_path: Path):
    (tmp_path / "a.py").write_text("nothing here")
    out = grep_search(tmp_path, "nonexistent-pattern")
    assert "No matches" in out


def test_grep_search_invalid_regex(tmp_path: Path):
    with pytest.raises(ValueError):
        grep_search(tmp_path, "[invalid")


def test_grep_search_skips_excluded_dirs(tmp_path: Path):
    skipdir = tmp_path / "node_modules"
    skipdir.mkdir()
    (skipdir / "x.txt").write_text("secret-value")
    (tmp_path / "ok.txt").write_text("secret-value")
    out = grep_search(tmp_path, "secret-value")
    assert "ok.txt" in out
    assert "node_modules" not in out


def test_grep_search_max_results(tmp_path: Path):
    p = tmp_path / "long.txt"
    p.write_text("\n".join(["match"] * 50))
    out = grep_search(tmp_path, "match", max_results=5)
    assert "truncated" in out


def test_grep_search_when_workdir_name_matches_skip_dir(tmp_path: Path):
    """Regression: working dir whose absolute path contains a SKIP_DIR_NAMES
    component must NOT cause every file to be silently skipped."""
    workdir = tmp_path / "build" / "myproj"
    workdir.mkdir(parents=True)
    (workdir / "main.py").write_text("print('hello-world')\n")
    out = grep_search(workdir, r"hello-world")
    assert "main.py" in out
    assert "No matches" not in out


def test_grep_search_still_skips_excluded_subdirs_under_matching_workdir(tmp_path: Path):
    """The fix above must not regress the original SKIP_DIR_NAMES behavior."""
    workdir = tmp_path / "build" / "myproj"
    workdir.mkdir(parents=True)
    (workdir / "ok.py").write_text("token-x\n")
    excluded = workdir / "node_modules" / "leaf"
    excluded.mkdir(parents=True)
    (excluded / "x.py").write_text("token-x\n")
    out = grep_search(workdir, r"token-x")
    assert "ok.py" in out
    assert "node_modules" not in out
