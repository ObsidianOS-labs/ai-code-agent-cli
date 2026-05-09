from pathlib import Path

from ai_code_agent.tools.dispatcher import ToolContext, dispatch


def test_dispatch_get_files_info(tmp_path: Path):
    (tmp_path / "a.txt").write_text("x")
    res = dispatch("get_files_info", {"directory": "."}, ToolContext(working_dir=tmp_path))
    assert not res.is_error
    assert "a.txt" in res.output


def test_dispatch_unknown_tool(tmp_path: Path):
    res = dispatch("bogus_tool", {}, ToolContext(working_dir=tmp_path))
    assert res.is_error
    assert "Unknown tool" in res.output


def test_dispatch_missing_arg(tmp_path: Path):
    res = dispatch("get_file_content", {}, ToolContext(working_dir=tmp_path))
    assert res.is_error
    assert "Missing required argument" in res.output


def test_dispatch_captures_exception(tmp_path: Path):
    res = dispatch(
        "get_file_content", {"file_path": "missing.txt"}, ToolContext(working_dir=tmp_path)
    )
    assert res.is_error
    assert "FileNotFoundError" in res.output


def test_dispatch_write_then_read(tmp_path: Path):
    ctx = ToolContext(working_dir=tmp_path)
    write_res = dispatch("write_file", {"file_path": "hello.txt", "content": "yo"}, ctx)
    assert not write_res.is_error
    read_res = dispatch("get_file_content", {"file_path": "hello.txt"}, ctx)
    assert not read_res.is_error
    assert read_res.output == "yo"
