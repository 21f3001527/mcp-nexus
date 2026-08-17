import asyncio
from langchain_core.messages import HumanMessage
from agent.orchestrator import build_agent


async def run(query: str):
    agent = await build_agent()
    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
    for m in result["messages"]:
        print(f"--- {m.type} ---")
        print(m.content)
        print()


if __name__ == "__main__":
    query =query = "Ingest the docs, then tell me what the Knowledge server does and what the most recent commit was about."
    asyncio.run(run(query))