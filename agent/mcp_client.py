import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVERS_DIR = PROJECT_ROOT / "servers"

_base_dir = str(PROJECT_ROOT)
_python_executable = sys.executable

_env = {**os.environ, "MCP_NEXUS_BASE_DIR": _base_dir}

MCP_CONNECTIONS = {
    "filesystem": {
        "transport": "stdio",
        "command": _python_executable,
        "args": [str(SERVERS_DIR / "filesystem_server.py")],
        "env": _env,
    },
    "git": {
        "transport": "stdio",
        "command": _python_executable,
        "args": [str(SERVERS_DIR / "git_server.py")],
        "env": _env,
    },
    "knowledge": {
        "transport": "stdio",
        "command": _python_executable,
        "args": [str(SERVERS_DIR / "knowledge_server.py")],
        "env": _env,
    },
}


async def get_all_tools():
    client = MultiServerMCPClient(MCP_CONNECTIONS)
    tools = await client.get_tools()
    return tools