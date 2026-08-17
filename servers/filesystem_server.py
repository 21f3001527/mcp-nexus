"""
Filesystem MCP Server
----------------------
Exposes filesystem operations (list, read, search) as MCP tools.
All operations are sandboxed to BASE_DIR to prevent path traversal
outside the intended project directory.
"""

import os
import fnmatch
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("filesystem-server")


# Sandbox root: the project directory this server is allowed to touch.
# Change this to the target repo/project path when running the server.
BASE_DIR = Path(os.environ.get("MCP_NEXUS_BASE_DIR", ".")).resolve()


SENSITIVE_FILE_PATTERNS = (
    ".env", ".env.local", ".env.production", ".pem", ".key",
    "credentials", "secrets", ".npmrc", ".pypirc", "id_rsa", "id_ed25519",
)


def _resolve_safe_path(relative_path: str) -> Path:
    """
    Resolve a user-supplied relative path against BASE_DIR and ensure
    the final path does not escape BASE_DIR (blocks '..' traversal).
    Raises ValueError if the path is outside the sandbox.
    """
    candidate = (BASE_DIR / relative_path).resolve()
    if BASE_DIR not in candidate.parents and candidate != BASE_DIR:
        raise ValueError(
            f"Access denied: '{relative_path}' resolves outside the allowed "
            f"project directory."
        )
    return candidate

def _is_sensitive(path: Path) -> bool:
    name_lower = path.name.lower()
    return any(pattern in name_lower for pattern in SENSITIVE_FILE_PATTERNS)

@mcp.tool()
def list_files(path: str = ".") -> str:
    """
    List files and directories at the given relative path inside the
    project. Returns a simple tree-like listing (one entry per line).

    Args:
        path: Relative path inside the project directory (default: root).
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return str(e)

    if not target.exists():
        return f"Error: path '{path}' does not exist."
    if not target.is_dir():
        return f"Error: path '{path}' is not a directory."

    entries = []
    for item in sorted(target.iterdir()):
        if item.name in (".git", "__pycache__", ".venv", "node_modules"):
            continue
        marker = "DIR " if item.is_dir() else "FILE"
        entries.append(f"[{marker}] {item.relative_to(BASE_DIR)}")

    if not entries:
        return f"'{path}' is empty."

    return "\n".join(entries)


@mcp.tool()
def read_file(path: str, max_chars: int = 5000) -> str:
    """
    Read the contents of a text file inside the project.

    Args:
        path: Relative path to the file inside the project directory.
        max_chars: Maximum number of characters to return (default 5000)
                   to avoid flooding the agent's context window.
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return str(e)

    if not target.exists():
        return f"Error: file '{path}' does not exist."
    if target.is_dir():
        return f"Error: '{path}' is a directory, not a file."
    if _is_sensitive(target):
        return f"Error: '{path}' is a sensitive file and cannot be read through this tool."
    

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {e}"

    truncated = len(content) > max_chars
    content = content[:max_chars]

    if truncated:
        content += f"\n\n... [truncated, showing first {max_chars} characters]"

    return content


@mcp.tool()
def search_files(pattern: str, path: str = ".") -> str:
    """
    Search for files whose name matches a glob-style pattern
    (e.g. '*.py', 'README*') within the given directory, recursively.

    Args:
        pattern: Glob pattern to match file names against (e.g. '*.py').
        path: Relative directory to start searching from (default: root).
    """
    try:
        target = _resolve_safe_path(path)
    except ValueError as e:
        return str(e)

    if not target.exists() or not target.is_dir():
        return f"Error: '{path}' is not a valid directory."

    matches = []
    skip_dirs = {".git", "__pycache__", ".venv", "node_modules"}

    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fnmatch.fnmatch(fname, pattern):
                full_path = Path(root) / fname
                matches.append(str(full_path.relative_to(BASE_DIR)))

    if not matches:
        return f"No files matching '{pattern}' found under '{path}'."

    return "\n".join(sorted(matches))


if __name__ == "__main__":
    mcp.run(transport="stdio")