"""Orchestration script for Kolibri ETL ingestion (Graph + Vectors)."""

from contextlib import suppress
from pathlib import Path
from typing import cast

import kuzu

from dt_bridge.etl.kolibri_extractor import KolibriTopicExtractor
from dt_bridge.etl.transcript_vectorizer import KolibriFileMetadata, TranscriptVectorizer


def ingest() -> None:
    """Execute the full knowledge ingestion ritual."""
    # 1. Paths
    base_path = Path("dt-bridge/data")
    db_path = base_path / "african_storybook.sqlite3"
    content_dir = base_path / "kolibri_content"
    kuzu_path = base_path / "knowledge_graph"
    lancedb_path = base_path / "semantic_memory"

    if not db_path.exists():
        print("❌ Kolibri database not found. Run seed_mock_kolibri.py first.")
        return

    # 2. Graph Ingestion (KuzuDB)
    print(f"🚀 Initializing Knowledge Graph at {kuzu_path}...")
    db = kuzu.Database(str(kuzu_path))
    conn = kuzu.Connection(db)

    print("🧹 Extracting and Loading Topic Tree...")
    extractor = KolibriTopicExtractor(str(db_path), conn)
    # We clear the graph first for idempotency
    with suppress(Exception):
        conn.execute("MATCH (n) DETACH DELETE n")
    extractor.extract_and_load()

    # 3. Vector Ingestion (LanceDB)
    print(f"🧠 Initializing Semantic Memory at {lancedb_path}...")
    vectorizer = TranscriptVectorizer(str(content_dir), str(lancedb_path))

    # Mock file metadata matching our seed script
    file_data: list[KolibriFileMetadata] = [
        {"id": "f1", "checksum": "gravity_checksum", "node_id": "gravity"},
        {"id": "f2", "checksum": "fractions_checksum", "node_id": "fractions"},
    ]

    print("✨ Vectorizing and Loading Transcripts...")
    vectorizer.process_transcripts(file_data)

    # 4. Final Verification
    query_res = conn.execute("MATCH (n:ContentNode) RETURN count(n)")
    res = cast("kuzu.QueryResult", query_res)
    graph_count = 0
    if res.has_next():
        row = cast("list[object]", res.get_next())
        graph_count = int(str(row[0]))

    vector_count = 0
    if "transcripts" in vectorizer.db.list_tables().tables:
        vector_count = len(vectorizer.db.open_table("transcripts").to_pandas())

    print("✅ Ingestion Complete!")
    print(f"📊 Graph Nodes: {graph_count}")
    print(f"📖 Vector Chunks: {vector_count}")

if __name__ == "__main__":
    ingest()
