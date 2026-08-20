"""
Quick CLI for debugging the MCP Nexus agent without the Streamlit UI.

Prints the full LangGraph message trace, including which tools were
called and their raw outputs — useful when something misbehaves and
you want to see the agent's reasoning step by step.

Usage:
    python main.py "What does this project do?"
    python main.py "What changed in the last commit?" --repo /path/to/other/project
"""

import argparse
import asyncio

from langchain_core.messages import HumanMessage

from agent.orchestrator import build_agent


async def run(query: str, repo: str | None = None):
    agent = await build_agent(base_dir=repo)
    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})

    for m in result["messages"]:
        print(f"--- {m.type} ---")
        print(m.content)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Debug the MCP Nexus agent from the terminal."
    )
    parser.add_argument("query", help="Question to ask the agent")
    parser.add_argument(
        "--repo",
        default=None,
        help="Path to a local repo to analyze (defaults to MCP Nexus itself)",
    )
    args = parser.parse_args()

    asyncio.run(run(args.query, args.repo))


if __name__ == "__main__":
    main()