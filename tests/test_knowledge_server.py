import sys
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def kb_server(tmp_path, monkeypatch):
    docs_dir = tmp_path / "data" / "docs"
    docs_dir.mkdir(parents=True)

    (docs_dir / "about.md").write_text(
        "# Test Project\n\n"
        "This project uses FastAPI for the backend and PostgreSQL for storage. "
        "Authentication is handled with JWT tokens.\n\n"
        "## Deployment\n\n"
        "The project is deployed using Docker containers on AWS."
    )

    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.knowledge_server as module
    importlib.reload(module)

    return module, tmp_path


def test_ingest_docs_creates_index(kb_server):
    module, base = kb_server
    result = module.ingest_docs("data/docs")

    assert "Ingested 1 document" in result
    assert (base / "data" / "faiss_index" / "index.faiss").exists()
    assert (base / "data" / "faiss_index" / "metadata.json").exists()


def test_ingest_docs_no_files_found(tmp_path, monkeypatch):
    empty_docs = tmp_path / "data" / "docs"
    empty_docs.mkdir(parents=True)
    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.knowledge_server as module
    importlib.reload(module)

    result = module.ingest_docs("data/docs")
    assert "No .md or .txt files found" in result


def test_query_knowledge_before_ingest(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import servers.knowledge_server as module
    importlib.reload(module)

    result = module.query_knowledge("What framework is used?")
    assert "No knowledge base found" in result


def test_query_knowledge_returns_relevant_chunk(kb_server):
    module, base = kb_server
    module.ingest_docs("data/docs")

    result = module.query_knowledge("What backend framework does this project use?", top_k=3)

    assert "FastAPI" in result
    assert "score:" in result


def test_query_knowledge_filters_low_confidence(kb_server):
    module, base = kb_server
    module.ingest_docs("data/docs")

    result = module.query_knowledge("What is the airspeed velocity of an unladen swallow?", top_k=3)

    assert "No sufficiently relevant results" in result or "not available" in result.lower()