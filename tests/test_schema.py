from ai_code_agent.tools import TOOL_SCHEMAS
from ai_code_agent.tools.schema import get_schema


def test_all_six_tools_present():
    names = {t.name for t in TOOL_SCHEMAS}
    assert names == {
        "get_files_info",
        "get_file_content",
        "grep_search",
        "write_file",
        "run_command",
        "run_python_file",
    }


def test_schemas_have_required_fields():
    for tool in TOOL_SCHEMAS:
        assert tool.name
        assert tool.description
        assert tool.parameters["type"] == "object"
        assert "properties" in tool.parameters


def test_get_schema_lookup():
    assert get_schema("write_file").name == "write_file"


def test_get_schema_unknown():
    import pytest

    with pytest.raises(KeyError):
        get_schema("nope")
