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


if __name__ == "__main__":
    repo_url = "https://github.com/octocat/Hello-World"
    query = "List the files in this repo and show me the most recent commit."
    asyncio.run(run(repo_url, query))