import sys
import importlib
from pathlib import Path

import numpy as np
import pytest


class FakeModel:
    """Deterministic lightweight embedding model for unit tests."""

    def encode(self, texts, show_progress_bar=False):
        embeddings = []

        for text in texts:
            text = text.lower()

            # Relevant to the FastAPI/backend query
            if "fastapi" in text or "backend framework" in text:
                embeddings.append([1.0, 0.0, 0.0])

            # Deliberately unrelated to the test document
            elif "airspeed velocity" in text or "unladen swallow" in text:
                embeddings.append([0.0, 0.0, 1.0])

            # Other content
            else:
                embeddings.append([0.0, 1.0, 0.0])

        return np.array(embeddings, dtype="float32")


@pytest.fixture
def kb_server(tmp_path, monkeypatch):
    """Create an isolated knowledge-server environment for testing."""

    # Create temporary documentation directory
    docs_dir = tmp_path / "data" / "docs"
    docs_dir.mkdir(parents=True)

    # Create test documentation
    (docs_dir / "about.md").write_text(
        "# Test Project\n\n"
        "This project uses FastAPI for the backend and PostgreSQL for storage. "
        "Authentication is handled with JWT tokens.\n\n"
        "## Deployment\n\n"
        "The project is deployed using Docker containers on AWS.",
        encoding="utf-8",
    )

    # Point the knowledge server to the temporary test directory
    monkeypatch.setenv("MCP_NEXUS_BASE_DIR", str(tmp_path))

    # Make project root importable
    project_root = str(Path(__file__).resolve().parent.parent)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Reload module so BASE_DIR picks up the temporary directory
    import servers.knowledge_server as module

    importlib.reload(module)

    # Replace the real SentenceTransformer with the fake model.
    # This prevents model loading/downloading during tests.
    monkeypatch.setattr(
        module,
        "_get_model",
        lambda: FakeModel(),
    )

    return module, tmp_path


def test_ingest_docs_creates_index(kb_server):
    """Test that documents are ingested and the FAISS index is persisted."""

    module, base = kb_server

    result = module.ingest_docs("data/docs")

    assert "Ingested 1 document" in result

    assert (
        base / "data" / "faiss_index" / "index.faiss"
    ).exists()

    assert (
        base / "data" / "faiss_index" / "metadata.json"
    ).exists()


def test_ingest_docs_no_files_found(tmp_path, monkeypatch):
    """Test ingestion behavior when no supported documents exist."""

    empty_docs = tmp_path / "data" / "docs"
    empty_docs.mkdir(parents=True)

    monkeypatch.setenv(
        "MCP_NEXUS_BASE_DIR",
        str(tmp_path),
    )

    project_root = str(Path(__file__).resolve().parent.parent)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    import servers.knowledge_server as module

    importlib.reload(module)

    result = module.ingest_docs("data/docs")

    assert "No .md or .txt files found" in result


def test_query_knowledge_before_ingest(tmp_path, monkeypatch):
    """Test querying when no FAISS knowledge base exists."""

    monkeypatch.setenv(
        "MCP_NEXUS_BASE_DIR",
        str(tmp_path),
    )

    project_root = str(Path(__file__).resolve().parent.parent)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    import servers.knowledge_server as module

    importlib.reload(module)

    result = module.query_knowledge(
        "What framework is used?"
    )

    assert "No knowledge base found" in result


def test_query_knowledge_returns_relevant_chunk(kb_server):
    """Test that relevant documentation is retrieved."""

    module, base = kb_server

    # Build the test knowledge base
    module.ingest_docs("data/docs")

    # Query for information that exists in the document
    result = module.query_knowledge(
        "What backend framework does this project use?",
        top_k=3,
    )

    assert "FastAPI" in result
    assert "score:" in result


def test_query_knowledge_filters_low_confidence(kb_server):
    """Test that low-confidence retrievals are filtered out."""

    module, base = kb_server

    # Build the test knowledge base
    module.ingest_docs("data/docs")

    # Query for unrelated information
    result = module.query_knowledge(
        "What is the airspeed velocity of an unladen swallow?",
        top_k=3,
    )

    assert (
        "No sufficiently relevant results" in result
        or "not available" in result.lower()
    )