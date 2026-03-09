"""Verification script for LanceDB keyword search (FTS)."""

from contextlib import suppress
from pathlib import Path

import lancedb


def verify_search() -> None:
    """Verify that semantic memory is searchable."""
    lancedb_path = Path("dt-bridge/data/semantic_memory")
    db = lancedb.connect(str(lancedb_path))
    table = db.open_table("transcripts")

    # Create Full Text Search index
    with suppress(Exception):
        table.create_fts_index("text")

    query = "gravity"
    # Query using text search
    results = table.search(query, query_type="fts").limit(1).to_pandas()

    if not results.empty:
        print(f"🔍 Keyword Search for: '{query}'")
        print(f"📖 Result: {results.iloc[0]['text']}")
        print("✅ Semantic (Keyword) Memory is searchable.")
    else:
        print("❌ No results found in semantic memory.")

if __name__ == "__main__":
    verify_search()
