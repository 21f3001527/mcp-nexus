import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition

from agent.state import AgentState
from agent.mcp_client import get_all_tools

load_dotenv()

SYSTEM_PROMPT = """You are an AI assistant with access to tools that inspect a software project.

You can:
- list, read, and search files in the project (filesystem tools)
- inspect git commit history, diffs, and file history (git tools)
- ingest documentation and answer questions using semantic search (knowledge tools)

Use the available tools to gather evidence before answering. If a question requires
multiple tools, call them in sequence and combine the results into one clear answer.
If the knowledge base has not been ingested yet and a question needs it, call
ingest_docs first."""


async def build_agent():
    tools = await get_all_tools()

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(tools)

    def call_model(state: AgentState):
        messages = state["messages"]
        if not messages or messages[0].type != "system":
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()