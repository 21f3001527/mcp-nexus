# 🧠 MCP Nexus

### An Agentic AI Workspace Powered by the Model Context Protocol

<p align="center">

<img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
<img src="https://img.shields.io/badge/MCP-FastMCP-8B5CF6">
<img src="https://img.shields.io/badge/LangGraph-Agent-1C3C3C?logo=langchain">
<img src="https://img.shields.io/badge/LangChain-Orchestration-1C3C3C?logo=langchain">
<img src="https://img.shields.io/badge/LLM-gpt--oss--120b-412991">
<img src="https://img.shields.io/badge/Groq-LLM%20Inference-F55036">
<img src="https://img.shields.io/badge/FAISS-Vector%20Search-0468D7">
<img src="https://img.shields.io/badge/Sentence%20Transformers-Embeddings-00A67E">
<img src="https://img.shields.io/badge/GitPython-Git%20Operations-F05032?logo=git">
<img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit">
<img src="https://img.shields.io/badge/uv-Package%20Manager-6B5B95">

<br>

<img src="https://img.shields.io/badge/Multi--Server-MCP-8B5CF6">
<img src="https://img.shields.io/badge/RAG-Enabled-00A67E">
<img src="https://img.shields.io/badge/GitHub-Repositories-181717?logo=github">
<img src="https://img.shields.io/badge/Security-Hardened-2EA44F">
<img src="https://img.shields.io/badge/License-MIT-yellow">

</p>

---

## 🎯 What is MCP Nexus?

**MCP Nexus** is an agentic AI workspace that can understand and analyze software projects by combining **three specialized MCP servers** under a single **LangGraph agent**.

Give it your own project or a public GitHub repository and ask:

> 💬 **"What does this project do?"**
> 🔍 **"How does this function handle errors?"**
> 🌿 **"What changed in the last commit?"**

The agent decides which tools to use, gathers evidence, and produces a grounded answer.

---

## ✨ Key Features

|     | Feature                  | Description                                                |
| --- | ------------------------ | ---------------------------------------------------------- |
| 🤖  | **Agentic Analysis**     | LangGraph agent dynamically selects and chains MCP tools   |
| 📁  | **Codebase Exploration** | Browse, read and search project source code                |
| 🌿  | **Git Intelligence**     | Analyze commits, diffs and file history                    |
| 📚  | **RAG Knowledge**        | Semantic search across project documentation               |
| 🌐  | **GitHub Support**       | Clone and analyze any public GitHub repository             |
| 🛡️ | **Secure by Design**     | Path traversal protection and sensitive-file blocking      |
| 🎯  | **Grounded Answers**     | Responses are based on actual tool outputs and source code |
| 💾  | **Persistent Knowledge** | FAISS index survives server restarts                       |

---

## 🏗️ Architecture

```text
                         👤 User
                           │
                           ▼
                    🖥️ Streamlit Chat
                           │
                           ▼
                  🧠 LangGraph Agent
                  ┌─────────────────┐
                  │  gpt-oss-120b   │
                  │     via Groq    │
                  └────────┬────────┘
                           │
                    🔌 MCP Protocol
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
       📁 Filesystem   🌿 Git       📚 Knowledge
           MCP           MCP            MCP
             │             │             │
       Project Files   Git History   FAISS + Docs
```

### 🔄 Agent Flow

```text
        User Question
              │
              ▼
        🧠 LangGraph Agent
              │
              ▼
        Select MCP Tools
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
      📁     🌿     📚
     Files   Git    RAG
       │      │      │
       └──────┼──────┘
              ▼
        🧠 Agent Reasoning
              │
              ▼
       🎯 Grounded Answer
```

The agent can call **one or multiple MCP servers** depending on the question.

---

## 🔌 MCP Servers

### 📁 Filesystem MCP

Provides safe access to project files.

| Tool           | Purpose                          |
| -------------- | -------------------------------- |
| `list_files`   | Explore project directories      |
| `read_file`    | Read source files                |
| `search_files` | Search files using glob patterns |

**Security:** path traversal protection, sensitive-file denylist, and noise-directory filtering.

---

### 🌿 Git MCP

Provides Git repository intelligence.

| Tool                 | Purpose                          |
| -------------------- | -------------------------------- |
| `get_recent_commits` | Inspect recent commits           |
| `get_diff`           | Compare commits or refs          |
| `get_file_history`   | Track changes to a specific file |

Git inputs are validated and bounded, with explicit handling for invalid commit references.

---

### 📚 Knowledge MCP

Provides RAG-based semantic search over project documentation.

| Tool              | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `ingest_docs`     | Chunk and embed `.md` / `.txt` documentation |
| `query_knowledge` | Retrieve relevant documentation              |

**Embedding:** `all-MiniLM-L6-v2`
**Vector Store:** FAISS
**Chunking:** 500 characters with 50-character overlap
**Retrieval threshold:** `0.35`

Low-confidence results are discarded instead of being passed to the agent as reliable evidence.

---

## 🧠 Why MCP?

Without MCP, an agent would need custom integrations for every system it interacts with.

MCP provides a standardized interface:

```text
                 🧠 AI Agent
                     │
              Model Context Protocol
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   📁 Filesystem   🌿 Git       📚 Knowledge
```

Each server exposes focused capabilities as tools, while the agent decides **when and how to combine them**.

This makes MCP Nexus a practical demonstration of:

**MCP + Tool Calling + Agentic Reasoning + RAG + Codebase Analysis**

---

## 🛡️ Reliability & Security

The system was deliberately stress-tested after the initial implementation.

### 🔒 Security Hardening

* 🚫 Sensitive files such as `.env`, `.pem`, and `id_rsa` are blocked
* 🔐 Path traversal protection
* 📦 Repository sandboxing
* 🔢 Bounded Git query parameters
* 🧹 `.git`, `.venv`, and `__pycache__` filtered from exploration

### 🎯 Agent Reliability

Several real failure modes were identified and fixed:

| Problem                        | Fix                                    |
| ------------------------------ | -------------------------------------- |
| Agent attempted to read `.env` | Sensitive-file denylist                |
| Malformed tool calls           | Switched to `gpt-oss-120b`             |
| Weak multi-source grounding    | Strict evidence-grounding instructions |
| Agent skipped source code      | Direct source-code fallback            |
| Wildcard searches failed       | More reliable structured tool calling  |
| Incorrect model identity       | Explicit MCP Nexus identity            |
| System prompt repetition       | Non-disclosure instruction             |

> ⚠️ **Known limitation:** The `0.35` retrieval threshold is currently heuristic and should be validated against a larger evaluation dataset before production use.

---

## 🌐 Analyze Any Public GitHub Repository

MCP Nexus supports two modes:

### 🏠 Current Project

Leave the GitHub URL empty to analyze MCP Nexus itself.

### 🌍 Public Repository

Provide a public GitHub URL and MCP Nexus will:

```text
GitHub URL
    ↓
🔎 Validate
    ↓
📥 Shallow Clone
    ↓
📦 Local Sandbox
    ↓
🔌 Connect MCP Servers
    ↓
🧠 Analyze Repository
```

Repositories are cached so the same project does not need to be cloned repeatedly.

---

## 🛠️ Tech Stack

<p align="center">

<img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
<img src="https://img.shields.io/badge/MCP-FastMCP-8B5CF6">
<img src="https://img.shields.io/badge/LangGraph-1C3C3C?logo=langchain">
<img src="https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain">
<img src="https://img.shields.io/badge/Groq-F55036">
<img src="https://img.shields.io/badge/gpt--oss--120b-412991">
<img src="https://img.shields.io/badge/FAISS-0468D7">
<img src="https://img.shields.io/badge/Sentence--Transformers-00A67E">
<img src="https://img.shields.io/badge/GitPython-F05032?logo=git">
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit">
<img src="https://img.shields.io/badge/uv-6B5B95">

</p>

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure your Groq API key

Create `.env`:

```env
GROQ_API_KEY=your_key_here
```

### 3. Launch MCP Nexus

```bash
uv run streamlit run app.py
```

Then open the Streamlit interface and start exploring your project.

---

## 📂 Project Structure

```text
mcp-nexus/
│
├── 🧠 agent/
│   ├── state.py
│   ├── mcp_client.py
│   ├── orchestrator.py
│   └── repo_utils.py
│
├── 🔌 servers/
│   ├── filesystem_server.py
│   ├── git_server.py
│   └── knowledge_server.py
│
├── 🖥️ app.py
├── 📦 pyproject.toml
└── 📖 README.md
```

---

## 📊 Project Status

| Component                    | Status     |
| ---------------------------- | ---------- |
| 📁 Filesystem MCP            | ✅ Complete |
| 🌿 Git MCP                   | ✅ Complete |
| 📚 Knowledge MCP             | ✅ Complete |
| 🧠 LangGraph Agent           | ✅ Complete |
| 🌐 GitHub Repository Support | ✅ Complete |
| 🖥️ Streamlit UI             | ✅ Complete |
| 🛡️ Reliability Hardening    | ✅ Complete |
| 🧪 Automated Tests           | 🚧 Planned |
| 📈 Evaluation Suite          | 🚧 Planned |
| ☁️ Deployment                | 🚧 Planned |

---

## 🎯 Project Goal

MCP Nexus explores how **Model Context Protocol can give AI agents standardized access to multiple sources of software-project context**.

Instead of manually jumping between:

**📁 Files + 🌿 Git + 📚 Documentation**

the agent can reason across all three and determine which evidence it needs.

> **Build agents that don't just answer — they investigate.** 🧠🔍

---

### ⭐ MCP Nexus

**MCP • LangGraph • RAG • Tool Calling • Git Intelligence • Codebase Analysis**
