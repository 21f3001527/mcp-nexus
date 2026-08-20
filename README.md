# MCP Nexus

**An Agentic AI Workspace Powered by the Model Context Protocol**

<p align="center">
<img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
<img src="https://img.shields.io/badge/MCP-FastMCP-8B5CF6">
<img src="https://img.shields.io/badge/LangGraph-Agent-1C3C3C?logo=langchain">
<img src="https://img.shields.io/badge/Groq-gpt--oss--120b-F55036">
<img src="https://img.shields.io/badge/FAISS-Vector%20Search-0468D7">
<img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit">
<img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white">
<img src="https://img.shields.io/badge/License-MIT-yellow">
<br>
<img src="https://img.shields.io/badge/Server%20Tests-21%2F21%20passing-2EA44F">
<img src="https://img.shields.io/badge/Agent%20Evaluation-92.31%25-2EA44F">
<img src="https://img.shields.io/badge/Security-Hardened-2EA44F">
<img src="https://img.shields.io/badge/Deployment-Live-2EA44F">
</p>

🚀 **Deployed on Streamlit Community Cloud — live and ready to use:**
**🔗 [https://mcp-nexus-ai.streamlit.app](https://mcp-nexus-ai.streamlit.app)**

**[GitHub Repository](https://github.com/21f3001527/mcp-nexus)**

---

### Contents

[What is MCP Nexus](#what-is-mcp-nexus) · [Key Features](#key-features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Docker](#docker) · [Screenshots](#screenshots) · [Tech Stack](#tech-stack) · [MCP Servers](#mcp-servers) · [Reliability & Security](#reliability--security) · [Evaluation](#evaluation) · [Project Structure](#project-structure) · [Known Limitations](#known-limitations) · [Author](#author)

---

## What is MCP Nexus?

MCP Nexus is an agentic AI workspace that understands and analyzes software projects by combining three specialized MCP servers — Filesystem, Git, and Knowledge (RAG) — under a single LangGraph agent. Ask a natural-language question and the agent decides which tools and sources it needs, then produces a grounded answer.

```
"What does this project do?"                  "What changed in the last commit?"
"How does this function handle errors?"        "How does the Knowledge server retrieve information?"
```

Works on the current project or any public GitHub repo.

---

## Key Features

**Core Capabilities**
- **Agentic Analysis** — LangGraph agent dynamically selects and chains MCP tools
- **Codebase Exploration** — browse, read, and search project source code
- **Git Intelligence** — analyze commits, diffs, and file history
- **RAG Knowledge** — semantic search across project documentation
- **GitHub Support** — clone and analyze any public repository
- **Grounded Answers** — responses are based on actual tool outputs, not guesses

**Security & Reliability**
- **Secure by Design** — path traversal protection and sensitive-file blocking
- **Automated Evaluation** — 26-scenario suite (run via `evaluation/` scripts) testing tool selection, grounding, and security

**Deployment**
- **Containerized** — Docker-ready for consistent local or cloud deployment

---

## Architecture

```
      User → Streamlit Chat → LangGraph Agent (gpt-oss-120b via Groq)
                                      │
                                MCP Protocol
                  ┌───────────────────┼───────────────────┐
                  ▼                   ▼                   ▼
            Filesystem MCP        Git MCP           Knowledge MCP
            Project Files      Git History          FAISS + Docs
```

- The user asks a question in the Streamlit chat
- The LangGraph agent decides which MCP server(s) the question needs
- Each server returns real tool output — file contents, commit data, or retrieved documentation
- The agent grounds its answer in that output before responding

---

## Quick Start

```bash
git clone https://github.com/21f3001527/mcp-nexus.git
cd mcp-nexus
uv sync
echo "GROQ_API_KEY=your_key_here" > .env
uv run streamlit run app.py
```

Or just try the **[live demo](https://mcp-nexus-ai.streamlit.app)** — no setup required.

**Debugging without the UI** — `main.py` runs the agent directly from the terminal and prints the full message trace, including which tools were called:

```bash
uv run python main.py "What does this project do?"
uv run python main.py "What changed in the last commit?" --repo /path/to/other/project
```

**Testing against an external repo** — `test_clone_agent.py` verifies the full clone → agent pipeline works end-to-end on any public GitHub repo:

```bash
uv run python test_clone_agent.py https://github.com/octocat/Hello-World "List the files in this repo"
```

---

## Docker

```bash
docker build -t mcp-nexus .
docker run --env-file .env -p 8502:8501 mcp-nexus
```

Open **http://localhost:8502** — Streamlit runs inside the container on port 8501, mapped to 8502 on the host.

---

## Screenshots

### Landing Page
<p align="center">
  <img src="assets/landing-page.png" width="900" alt="MCP Nexus landing page">
</p>

### Repository Chat
<p align="center">
  <img src="assets/repository-chat.png" width="900" alt="MCP Nexus repository analysis chat">
</p>

### Demo
<p align="center">
  <img src="assets/mcp-nexus-demo.gif" width="900" alt="MCP Nexus demo">
</p>

---

## Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| Language | Python 3.12 | Application development |
| Tool Protocol | FastMCP | Standardized MCP server/tool interface |
| Agent Orchestration | LangGraph | Agent state and tool-calling workflow |
| LLM Orchestration | LangChain | LLM workflows and chains |
| LLM Inference | Groq (gpt-oss-120b) | Fast LLM inference |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) | Local document embeddings |
| Vector Store | FAISS | Persistent semantic retrieval |
| Git Operations | GitPython | Commit, diff, and history analysis |
| UI | Streamlit | Interactive chat interface |
| Containerization | Docker | Reproducible builds and deployment |
| Package Management | uv | Dependency and environment management |

---

## MCP Servers

| Server | Tools | Notes |
|---|---|---|
| **Filesystem** | `list_files`, `read_file`, `search_files` | Path traversal protection, sensitive-file denylist, repo sandboxing |
| **Git** | `get_recent_commits`, `get_diff`, `get_file_history` | Validated, bounded inputs; handles invalid refs safely |
| **Knowledge** | `ingest_docs`, `query_knowledge` | RAG over `.md`/`.txt` docs — chunking → embeddings → FAISS → 0.35 similarity threshold |

Low-confidence retrieval results are discarded rather than passed to the agent as reliable evidence.

---

## Reliability & Security

Sensitive files (`.env`, `.pem`, `id_rsa`) are blocked, paths are sandboxed, and `.git`/`.venv`/`__pycache__` are filtered from exploration. Several real failure modes were found and fixed during development — e.g. malformed tool calls (fixed by switching to gpt-oss-120b), weak multi-source grounding (fixed with stricter evidence instructions), and repeated doc ingestion (fixed with idempotent handling).

> The 0.35 retrieval threshold is heuristic and should be validated against a larger dataset before production use.

---

## Evaluation

Automated evaluation is available through the `evaluation/` scripts. This is a development and testing component — it runs from the command line, not from the deployed app.

Two layers of testing: **server tests** check whether tools work correctly; **agent evaluation** checks whether the agent *uses* them correctly (tool selection, grounding, multi-tool reasoning, security boundaries).

| Suite | Result |
|---|---|
| MCP Server Tests | 21/21 passing |
| Agent Evaluation (26 scenarios) | 24 passed · 2 failed · 92.31% |

The 2 failures (`filesystem_path_traversal`, `sensitive_file_block`) happen because the agent *correctly refuses* the sensitive request before ever calling `read_file` — the test expected the tool call, so it's flagged as a failure even though nothing was exposed. Results aren't adjusted to force a perfect score; a failed case is treated as a signal, not a bug to hide.

Evaluation is **resumable** — progress saves after every test, so rate limits or timeouts don't require restarting the whole suite.

```bash
uv run pytest tests/ -v                    # server tests
uv run python evaluation/run_tests.py      # agent evaluation
```

Results: `evaluation/results/latest.json`, `evaluation/results/summary.json`

---

## Project Structure

```
mcp-nexus/
├── agent/            state.py, mcp_client.py, orchestrator.py, repo_utils.py
├── servers/          filesystem_server.py, git_server.py, knowledge_server.py
├── tests/            test_filesystem_server.py, test_git_server.py, test_knowledge_server.py
├── evaluation/        run_tests.py, test_cases.json, results/
├── data/
│   ├── docs/          # Project documentation used by the Knowledge server
│   └── faiss_index/   # Generated FAISS index — ignored by Git, built locally on first run
├── assets/            demo GIF and screenshots used in this README
├── app.py             Streamlit app (primary entry point)
├── main.py            CLI for debugging the agent from the terminal
├── test_clone_agent.py  CLI for testing the clone → agent pipeline on an external repo
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Known Limitations

- Retrieval threshold (0.35) is heuristic, not yet validated at scale
- Agent tool-calling reliability depends on the selected LLM
- Very large repositories may need extra optimization for cloning/indexing
- 26-scenario eval suite is broad but still relatively small

---

## Author

**Rajeev Kumar**
B.S. Data Science and Applications — IIT Madras

[GitHub](https://github.com/21f3001527) · [LinkedIn](https://linkedin.com/in/rajeev245)

---

## License

MIT