"""
Debug script that verifies the full clone -> agent pipeline works
end-to-end against a real public GitHub repository.

Useful for checking that repo cloning, MCP server startup, and the
agent's tool-calling all work together on a fresh repo, separate
from testing against MCP Nexus's own codebase.

Usage:
    python test_clone_agent.py https://github.com/octocat/Hello-World "List the files in this repo"
    python test_clone_agent.py https://github.com/owner/repo "What changed in the last commit?"
"""

import argparse
import asyncio

from langchain_core.messages import HumanMessage

from agent.orchestrator import build_agent
from agent.repo_utils import clone_repo


async def run(repo_url: str, query: str):
    print(f"Cloning {repo_url} ...")
    local_path = clone_repo(repo_url)
    print(f"Cloned to: {local_path}\n")

    agent = await build_agent(base_dir=str(local_path))
    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})

    for m in result["messages"]:
        print(f"--- {m.type} ---")
        print(m.content)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Debug the clone -> agent pipeline against a public GitHub repo."
    )
    parser.add_argument("repo_url", help="Public GitHub repository URL to clone")
    parser.add_argument("query", help="Question to ask the agent about the cloned repo")
    args = parser.parse_args()

    asyncio.run(run(args.repo_url, args.query))


if __name__ == "__main__":
    main()