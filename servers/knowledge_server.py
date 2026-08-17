import os
import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("knowledge-server")

BASE_DIR = Path(os.environ.get("MCP_NEXUS_BASE_DIR", ".")).resolve()
INDEX_DIR = BASE_DIR / "data" / "faiss_index"
INDEX_PATH = INDEX_DIR / "index.faiss"
METADATA_PATH = INDEX_DIR / "metadata.json"

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def _resolve_safe_path(relative_path: str) -> Path:
    candidate = (BASE_DIR / relative_path).resolve()
    if BASE_DIR not in candidate.parents and candidate != BASE_DIR:
        raise ValueError(f"Access denied: '{relative_path}' resolves outside the project directory.")
    return candidate


def _load_documents(target_dir: Path) -> list[dict]:
    docs = []
    for ext in ("*.md", "*.txt"):
        for file_path in target_dir.rglob(ext):
            if any(part in (".git", "__pycache__", ".venv", "node_modules") for part in file_path.parts):
                continue
            text = file_path.read_text(encoding="utf-8", errors="replace")
            docs.append({"source": str(file_path.relative_to(BASE_DIR)), "text": text})
    return docs


@mcp.tool()
def ingest_docs(path: str = "data/docs") -> str:
    """Ingest .md and .txt files from a directory, chunk them, embed them, and persist a FAISS index for later querying."""
    try:
        target_dir = _resolve_safe_path(path)
    except ValueError as e:
        return str(e)

    if not target_dir.exists() or not target_dir.is_dir():
        return f"Error: '{path}' is not a valid directory."

    documents = _load_documents(target_dir)
    if not documents:
        return f"No .md or .txt files found under '{path}'."

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in documents:
        for chunk_text in splitter.split_text(doc["text"]):
            if chunk_text.strip():
                chunks.append({"source": doc["source"], "text": chunk_text})

    if not chunks:
        return "No content to index after chunking."

    model = _get_model()
    embeddings = model.encode([c["text"] for c in chunks], show_progress_bar=False)
    embeddings = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    return (
        f"Ingested {len(documents)} document(s) into {len(chunks)} chunks. "
        f"Index persisted to '{INDEX_PATH.relative_to(BASE_DIR)}'."
    )


@mcp.tool()
def query_knowledge(question: str, top_k: int = 3) -> str:
    """Query the persisted knowledge base and return the most relevant chunks for a question."""
    top_k = max(1, min(top_k, 10))

    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        return "No knowledge base found. Run ingest_docs() first."

    try:
        index = faiss.read_index(str(INDEX_PATH))
        chunks = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        return f"Error loading knowledge base: {e}"

    if index.ntotal == 0 or not chunks:
        return "Knowledge base is empty. Run ingest_docs() first."

    model = _get_model()
    query_vec = model.encode([question])
    query_vec = np.array(query_vec, dtype="float32")
    faiss.normalize_L2(query_vec)

    k = min(top_k, index.ntotal)
    scores, indices = index.search(query_vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = chunks[idx]
        results.append(
            f"[score: {score:.3f}] source: {chunk['source']}\n{chunk['text']}"
        )

    if not results:
        return "No relevant results found."

    return "\n\n---\n\n".join(results)


if __name__ == "__main__":
    mcp.run(transport="stdio")