# MCP Nexus

MCP Nexus is an agentic AI workspace powered by the Model Context Protocol. It allows an AI agent to discover and interact with multiple external systems through a standardized interface, instead of relying on custom integrations for each system.

## Architecture

The system consists of three MCP servers, each exposing a different set of capabilities. The Filesystem server allows the agent to list files, read file contents, and search for files by pattern within a project directory. The Git server allows the agent to inspect commit history, compare changes between commits, and trace the history of individual files. The Knowledge server allows the agent to ingest documentation into a vector index and retrieve relevant information using semantic search.

## Filesystem Server

The Filesystem server is sandboxed to a base directory to prevent path traversal outside the intended project folder. It exposes three tools: list_files for directory listings, read_file for reading file contents with truncation safeguards, and search_files for finding files that match a glob pattern.

## Git Server

The Git server uses GitPython to inspect a repository's history. It exposes get_recent_commits to list the most recent commits, get_diff to compare two commits, and get_file_history to trace how a specific file has changed over time. All numeric inputs are bounded to prevent excessive resource usage, and file paths are validated to stay within the project directory.

## Knowledge Server

The Knowledge server implements retrieval-augmented generation over local documentation. It uses a recursive character text splitter to chunk documents while preserving paragraph and sentence boundaries, then embeds the chunks using a sentence-transformers model. The resulting vectors are stored in a FAISS index that persists to disk, so the knowledge base does not need to be rebuilt every time the server restarts.

## Agent Orchestration

A LangGraph agent acts as the MCP client. It connects to all three servers, discovers their available tools, and decides which tools to call based on the user's natural language request. For a query that touches multiple systems, the agent combines the results from each tool call into a single coherent answer.

## Why MCP

Before MCP, connecting an AI application to external systems required a custom integration for every system. MCP standardizes this interaction, similar to how a universal port standardizes how devices connect to a computer. This makes AI agent tooling easier to build, reuse, and maintain as the number of connected systems grows.