import os
import sys
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def fs_server(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.filesystem_server as module
    importlib.reload(module)
    return module, tmp_path


def test_list_files_shows_created_files(fs_server):
    module, base = fs_server
    (base / "hello.txt").write_text("hi")
    (base / "subdir").mkdir()

    result = module.list_files(".")

    assert "hello.txt" in result
    assert "subdir" in result


def test_list_files_nonexistent_path(fs_server):
    module, base = fs_server
    result = module.list_files("does_not_exist")
    assert "does not exist" in result


def test_read_file_returns_content(fs_server):
    module, base = fs_server
    (base / "note.txt").write_text("hello world")

    result = module.read_file("note.txt")

    assert result == "hello world"


def test_read_file_truncates_large_content(fs_server):
    module, base = fs_server
    (base / "big.txt").write_text("x" * 1000)

    result = module.read_file("big.txt", max_chars=100)

    assert len(result) < 1000
    assert "truncated" in result


def test_read_file_blocks_sensitive_files(fs_server):
    module, base = fs_server
    (base / ".env").write_text("SECRET_KEY=12345")

    result = module.read_file(".env")

    assert "sensitive" in result.lower()
    assert "SECRET_KEY" not in result


def test_read_file_blocks_path_traversal(fs_server):
    module, base = fs_server
    result = module.read_file("../../etc/passwd")
    assert "Access denied" in result


def test_search_files_finds_matching_pattern(fs_server):
    module, base = fs_server
    (base / "a.py").write_text("")
    (base / "b.py").write_text("")
    (base / "c.txt").write_text("")

    result = module.search_files("*.py")

    assert "a.py" in result
    assert "b.py" in result
    assert "c.txt" not in result


def test_search_files_no_match(fs_server):
    module, base = fs_server
    result = module.search_files("*.nonexistent")
    assert "No files matching" in result