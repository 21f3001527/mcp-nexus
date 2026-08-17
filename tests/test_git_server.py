import sys
import importlib
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture
def git_server(tmp_path, monkeypatch):
    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    (tmp_path / "file1.txt").write_text("first version")
    repo.index.add(["file1.txt"])
    first_commit = repo.index.commit("First commit")

    (tmp_path / "file1.txt").write_text("second version")
    repo.index.add(["file1.txt"])
    second_commit = repo.index.commit("Second commit")

    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.git_server as module
    importlib.reload(module)

    return module, tmp_path, first_commit, second_commit


def test_get_recent_commits_returns_commits(git_server):
    module, base, first, second = git_server
    result = module.get_recent_commits(5)

    assert "First commit" in result
    assert "Second commit" in result
    assert first.hexsha[:7] in result
    assert second.hexsha[:7] in result


def test_get_recent_commits_clamps_n(git_server):
    module, base, first, second = git_server
    result = module.get_recent_commits(9999)
    assert "Error" not in result


def test_get_recent_commits_not_a_repo(tmp_path, monkeypatch):
    empty_dir = tmp_path / "not_a_repo"
    empty_dir.mkdir()
    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(empty_dir))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.git_server as module
    importlib.reload(module)

    result = module.get_recent_commits(5)
    assert "not a valid Git repository" in result


def test_get_diff_between_commits(git_server):
    module, base, first, second = git_server
    result = module.get_diff(first.hexsha, second.hexsha)

    assert "first version" in result
    assert "second version" in result


def test_get_diff_invalid_commit(git_server):
    module, base, first, second = git_server
    result = module.get_diff("not_a_real_commit", "HEAD")
    assert "could not resolve" in result.lower() or "error" in result.lower()


def test_get_file_history_returns_commits(git_server):
    module, base, first, second = git_server
    result = module.get_file_history("file1.txt")

    assert "First commit" in result
    assert "Second commit" in result


def test_get_file_history_untracked_file(git_server):
    module, base, first, second = git_server
    result = module.get_file_history("never_existed.txt")
    assert "No commit history found" in result


def test_get_file_history_blocks_path_traversal(git_server):
    module, base, first, second = git_server
    result = module.get_file_history("../../etc/passwd")
    assert "Access denied" in result