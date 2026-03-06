"""Test suite for dt-bridge ETL."""

import sqlite3
from pathlib import Path
from typing import cast

import kuzu
import pytest

from dt_bridge.etl.kolibri_extractor import KolibriTopicExtractor
from dt_bridge.etl.transcript_vectorizer import KolibriFileMetadata, TranscriptVectorizer


@pytest.fixture
def kuzu_db(tmp_path: Path) -> kuzu.Database:
    """Initialize a mock KuzuDB."""
    db_path = tmp_path / "kuzu_test"
    return kuzu.Database(str(db_path))


def test_kolibri_topic_extractor(mock_kolibri_db: Path, kuzu_db: kuzu.Database) -> None:
    """Test the KolibriTopicExtractor."""
    conn = kuzu.Connection(kuzu_db)
    extractor = KolibriTopicExtractor(str(mock_kolibri_db), conn)

    # Run extraction
    extractor.extract_and_load()

    # Verify ContentNode vertices
    query_result = conn.execute("MATCH (n:ContentNode) RETURN n.id, n.title, n.kind ORDER BY n.id")
    result = cast("kuzu.QueryResult", query_result)
    rows: list[list[str]] = []
    while result.has_next():
        row = result.get_next()
        rows.append([str(x) for x in row])

    assert len(rows) == 4
    assert rows[0][0] == "root"
    assert rows[0][1] == "Root Topic"
    assert rows[0][2] == "topic"

    # Verify Parent-Child relationships
    query_result = conn.execute("MATCH (p:ContentNode)-[:HAS_CHILD]->(c:ContentNode) RETURN p.id, c.id")
    result = cast("kuzu.QueryResult", query_result)
    rels: list[list[str]] = []
    while result.has_next():
        row = result.get_next()
        rels.append([str(x) for x in row])

    assert len(rels) == 3
    # Check if (root, sub1), (sub1, vid1), (sub1, vid2) exist
    rel_set = {(r[0], r[1]) for r in rels}
    assert ("root", "sub1") in rel_set
    assert ("sub1", "vid1") in rel_set
    assert ("sub1", "vid2") in rel_set


def test_transcript_vectorizer(mock_kolibri_content: Path, tmp_path: Path) -> None:
    """Test the TranscriptVectorizer."""
    lancedb_dir = tmp_path / "lancedb"
    vectorizer = TranscriptVectorizer(str(mock_kolibri_content), str(lancedb_dir))

    file_data: list[KolibriFileMetadata] = [
        {"id": "file1", "checksum": "abcd123", "node_id": "vid1"},
    ]

    vectorizer.process_transcripts(file_data)

    # Search (will do a scan if no embeddings, which is fine for test)
    assert "transcripts" in vectorizer.db.list_tables().tables
    table = vectorizer.db.open_table("transcripts")
    data = table.to_pandas()
    assert len(data) >= 1
    assert "gravity" in data.iloc[0]["text"].lower()


def test_kolibri_topic_extractor_empty(tmp_path: Path, kuzu_db: kuzu.Database) -> None:
    """Test extractor with empty database."""
    db_path = tmp_path / "empty.sqlite3"
    conn = sqlite3.connect(db_path)
    # Need all columns used in query
    conn.execute(
        "CREATE TABLE content_contentnode ("
        "id VARCHAR(32), title VARCHAR(32), kind VARCHAR(32), description TEXT, "
        "channel_id VARCHAR(32), content_id VARCHAR(32), available BOOLEAN, parent_id VARCHAR(32))",
    )
    conn.close()

    conn_kuzu = kuzu.Connection(kuzu_db)
    extractor = KolibriTopicExtractor(str(db_path), conn_kuzu)
    extractor.extract_and_load()

    # Re-init should not fail (covers schema already exists paths)
    extractor2 = KolibriTopicExtractor(str(db_path), conn_kuzu)
    assert extractor2 is not None


def test_transcript_vectorizer_missing_file(
    mock_kolibri_content: Path, tmp_path: Path,
) -> None:
    """Test vectorizer with missing file."""
    lancedb_dir = tmp_path / "lancedb_missing"
    vectorizer = TranscriptVectorizer(str(mock_kolibri_content), str(lancedb_dir))

    # checksum that doesn't exist
    file_data: list[KolibriFileMetadata] = [
        {"id": "file2", "checksum": "nonexistent", "node_id": "vid2"},
    ]

    vectorizer.process_transcripts(file_data)
    # Table should not be created if no chunks
    assert "transcripts" not in vectorizer.db.list_tables().tables
