"""Test suite for Kolibri retrieval service."""

from pathlib import Path
from typing import cast
from unittest.mock import patch

import kuzu
import pandas as pd
import pytest

from dt_bridge.etl.kolibri_extractor import KolibriTopicExtractor
from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer
from dt_bridge.retrieval.librarian import Librarian


@pytest.fixture
def kuzu_db(tmp_path: Path) -> kuzu.Database:
    """Initialize a mock KuzuDB."""
    db_path = tmp_path / "kuzu_retrieval"
    return kuzu.Database(str(db_path))


@pytest.fixture
def mock_vectorizer(tmp_path: Path) -> TranscriptVectorizer:
    """Create a mock TranscriptVectorizer."""
    lancedb_dir = tmp_path / "lancedb_retrieval"
    return TranscriptVectorizer(str(tmp_path), str(lancedb_dir))


def test_librarian_retrieval(
    mock_kolibri_db: Path, kuzu_db: kuzu.Database, mock_vectorizer: TranscriptVectorizer,
) -> None:
    """Test full Librarian retrieval capabilities."""
    conn = kuzu.Connection(kuzu_db)

    # 1. Ingest data
    extractor = KolibriTopicExtractor(str(mock_kolibri_db), conn)
    extractor.extract_and_load()

    # 2. Initialize Librarian
    librarian = Librarian(conn, mock_vectorizer)

    # 3. Test node retrieval
    root_node = librarian.get_node_by_id("root")
    assert root_node is not None
    assert root_node["n.title"] == "Root Topic"
    assert root_node["n.kind"] == "topic"

    # 4. Test children retrieval
    children = librarian.get_children("root")
    assert len(children) == 1
    assert children[0]["c.id"] == "sub1"

    # 5. Test parent retrieval
    parent = librarian.get_parent("sub1")
    assert parent is not None
    assert parent["p.id"] == "root"

    # 6. Test semantic search (mocked)
    with patch.object(
        mock_vectorizer,
        "search",
        return_value=pd.DataFrame(
            [{"text": "gravity", "node_id": "vid1", "checksum": "abc"}],
        ),
    ):
        results = librarian.semantic_search("gravity")
        assert len(results) == 1
        assert results[0]["text"] == "gravity"

    # 7. Test full context
    with patch.object(
        mock_vectorizer,
        "search",
        return_value=pd.DataFrame(
            [{"text": "gravity", "node_id": "vid1", "checksum": "abc"}],
        ),
    ):
        context = librarian.get_context_for_lesson("vid1")
        assert "node" in context
        assert "parent" in context
        assert "transcripts" in context
        # architectural: allowed-object (Comprehensive context dictionary)
        node_data = cast("dict[str, str]", context["node"])
        assert node_data["n.id"] == "vid1"

    # 8. Test context for non-existent node
    context_missing = librarian.get_context_for_lesson("nonexistent")
    assert context_missing == {}
