import os
from pathlib import Path
from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError, NoSuchPathError
from gitdb.exc import BadName
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("git-server")
BASE_DIR = Path(os.environ.get("MCP_NEXUS_BASE_DIR", ".")).resolve()


def _get_repo() -> Repo:
    return Repo(BASE_DIR)


def _resolve_safe_path(relative_path: str) -> Path:
    candidate = (BASE_DIR / relative_path).resolve()
    if BASE_DIR not in candidate.parents and candidate != BASE_DIR:
        raise ValueError(f"Access denied: '{relative_path}' resolves outside the project directory.")
    return candidate


@mcp.tool()
def get_recent_commits(n: int = 5) -> str:
    """List the n most recent commits with hash, author, date, and message."""
    n = max(1, min(n, 50))

    try:
        repo = _get_repo()
    except (InvalidGitRepositoryError, NoSuchPathError):
        return f"Error: '{BASE_DIR}' is not a valid Git repository."

    if repo.bare:
        return "Error: repository has no working tree."

    commits = list(repo.iter_commits(max_count=n))
    if not commits:
        return "No commits found."

    lines = []
    for c in commits:
        lines.append(
            f"{c.hexsha[:7]} | {c.committed_datetime.strftime('%Y-%m-%d %H:%M')} "
            f"| {c.author.name} | {c.message.strip().splitlines()[0]}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_diff(commit1: str, commit2: str = "HEAD") -> str:
    """Show the diff between two commits."""
    try:
        repo = _get_repo()
    except (InvalidGitRepositoryError, NoSuchPathError):
        return f"Error: '{BASE_DIR}' is not a valid Git repository."

    try:
        repo.commit(commit1)
        repo.commit(commit2)
    except BadName:
        return f"Error: could not resolve '{commit1}' or '{commit2}' to a commit."

    try:
        diff_text = repo.git.diff(commit1, commit2)
    except GitCommandError as e:
        return f"Error computing diff: {e}"

    if not diff_text.strip():
        return f"No differences found between '{commit1}' and '{commit2}'."

    max_chars = 6000
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars] + "\n\n...[truncated]"
    return diff_text


@mcp.tool()
def get_file_history(path: str, max_commits: int = 10) -> str:
    """Show commit history for a specific file."""
    max_commits = max(1, min(max_commits, 50))

    try:
        _resolve_safe_path(path)
    except ValueError as e:
        return str(e)

    try:
        repo = _get_repo()
    except (InvalidGitRepositoryError, NoSuchPathError):
        return f"Error: '{BASE_DIR}' is not a valid Git repository."

    commits = list(repo.iter_commits(paths=path, max_count=max_commits))
    if not commits:
        return f"No commit history found for '{path}'."

    lines = []
    for c in commits:
        lines.append(
            f"{c.hexsha[:7]} | {c.committed_datetime.strftime('%Y-%m-%d %H:%M')} "
            f"| {c.author.name} | {c.message.strip().splitlines()[0]}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")