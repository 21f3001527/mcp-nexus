import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from agent.orchestrator import build_agent
from agent.repo_utils import clone_repo, is_valid_github_url

st.set_page_config(page_title="MCP Nexus", page_icon="🧠", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "loaded_repo" not in st.session_state:
    st.session_state.loaded_repo = None


def run_async(coro):
    return asyncio.run(coro)


st.title("🧠 MCP Nexus")
st.caption("An agentic AI workspace powered by the Model Context Protocol")

with st.sidebar:
    st.header("Repository")
    repo_url = st.text_input(
        "GitHub URL (leave empty to analyze this project itself)",
        placeholder="https://github.com/owner/repo",
    )
    load_clicked = st.button("Load Repository", use_container_width=True)

    if st.session_state.loaded_repo:
        st.success(f"Loaded: {st.session_state.loaded_repo}")

    st.divider()
    st.markdown(
        "**Available tools**\n"
        "- Filesystem: list, read, search files\n"
        "- Git: commits, diffs, file history\n"
        "- Knowledge: ingest docs, semantic search"
    )

    if load_clicked:
        if repo_url.strip():
            if not is_valid_github_url(repo_url):
                st.error("That doesn't look like a valid GitHub URL.")
            else:
                with st.spinner(f"Cloning {repo_url} ..."):
                    try:
                        local_path = clone_repo(repo_url)
                        st.session_state.agent = run_async(
                            build_agent(base_dir=str(local_path))
                        )
                        st.session_state.loaded_repo = repo_url
                        st.session_state.messages = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to load repo: {e}")
        else:
            with st.spinner("Loading this project..."):
                st.session_state.agent = run_async(build_agent(base_dir=None))
                st.session_state.loaded_repo = "MCP Nexus (this project)"
                st.session_state.messages = []
                st.rerun()

if st.session_state.agent is None:
    st.info("Load a repository from the sidebar to get started.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about the repository...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                lc_messages = [
                    HumanMessage(content=m["content"]) if m["role"] == "user"
                    else AIMessage(content=m["content"])
                    for m in st.session_state.messages
                ]
                result = run_async(
                    st.session_state.agent.ainvoke({"messages": lc_messages})
                )
                final_message = result["messages"][-1]
                answer = final_message.content
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})