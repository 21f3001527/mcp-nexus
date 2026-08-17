import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVERS_DIR = PROJECT_ROOT / "servers"

_python_executable = sys.executable


def _build_connections(base_dir: str) -> dict:
    env = {**os.environ, "MCP_NEXUS_BASE_DIR": base_dir}
    return {
        "filesystem": {
            "transport": "stdio",
            "command": _python_executable,
            "args": [str(SERVERS_DIR / "filesystem_server.py")],
            "env": env,
        },
        "git": {
            "transport": "stdio",
            "command": _python_executable,
            "args": [str(SERVERS_DIR / "git_server.py")],
            "env": env,
        },
        "knowledge": {
            "transport": "stdio",
            "command": _python_executable,
            "args": [str(SERVERS_DIR / "knowledge_server.py")],
            "env": env,
        },
    }


async def get_all_tools(base_dir: str | None = None):
    if base_dir is None:
        base_dir = str(PROJECT_ROOT)
    connections = _build_connections(base_dir)
    client = MultiServerMCPClient(connections)
    tools = await client.get_tools()
    return tools