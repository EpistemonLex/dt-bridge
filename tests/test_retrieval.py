"""Test suite for Kolibri retrieval service (Verified Fakes + Dishka)."""

from pathlib import Path
from typing import cast

import kuzu
import pandas as pd
import pytest
from dishka import Provider, Scope, make_async_container, provide

from dt_bridge.etl.kolibri_extractor import KolibriTopicExtractor
from dt_bridge.interfaces import ITranscriptVectorizer
from dt_bridge.retrieval.librarian import Librarian


class FakeVectorizer:
    """Stateful fake for semantic search."""

    def __init__(self) -> None:
        """Initialize with empty results."""
        self.search_results: pd.DataFrame = pd.DataFrame()

    def search(self, query: str, limit: int = 5) -> pd.DataFrame:
        """Return canned search results."""
        _ = query # architectural: allowed-object
        _ = limit # architectural: allowed-object
        return self.search_results

class RetrievalTestProvider(Provider):
    """Provider for retrieval tests."""

    @provide(scope=Scope.APP)
    def get_vectorizer(self) -> ITranscriptVectorizer:
        """Return a fake vectorizer."""
        return FakeVectorizer()

@pytest.fixture
def kuzu_db(tmp_path: Path) -> kuzu.Database:
    """Initialize a mock KuzuDB."""
    db_path = tmp_path / "kuzu_retrieval"
    return kuzu.Database(str(db_path))

@pytest.mark.asyncio
async def test_librarian_retrieval(
    mock_kolibri_db: Path, kuzu_db: kuzu.Database,
) -> None:
    """Test full Librarian retrieval capabilities using Fake."""
    conn = kuzu.Connection(kuzu_db)
    container = make_async_container(RetrievalTestProvider())
    fake_vectorizer = await container.get(ITranscriptVectorizer)

    # 1. Ingest data
    extractor = KolibriTopicExtractor(str(mock_kolibri_db), conn)
    extractor.extract_and_load()

    # 2. Initialize Librarian (now depends on ITranscriptVectorizer)
    librarian = Librarian(conn, fake_vectorizer)


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

    # 6. Test semantic search (Using Fake)
    fake_vectorizer.search_results = pd.DataFrame(
        [{"text": "gravity", "node_id": "vid1", "checksum": "abc"}],
    )
    results = librarian.semantic_search("gravity")
    assert len(results) == 1
    assert results[0]["text"] == "gravity"

    # 7. Test full context
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

