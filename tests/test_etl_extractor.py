import sqlite3
import pytest
import kuzu
import os
from pathlib import Path
from dt_bridge.etl.kolibri_extractor import KolibriTopicExtractor

@pytest.fixture
def mock_kolibri_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "mock_channel.sqlite3"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create content_contentnode table
    cursor.execute("""
        CREATE TABLE content_contentnode (
            id VARCHAR(32) PRIMARY KEY,
            parent_id VARCHAR(32),
            channel_id VARCHAR(32),
            kind VARCHAR(20),
            title VARCHAR(200),
            description TEXT,
            content_id VARCHAR(32),
            available BOOLEAN,
            sort_order FLOAT
        )
    """)
    
    # Insert some mock data: Root Topic -> Subtopic -> Video
    nodes = [
        # id, parent_id, channel_id, kind, title, description, content_id, available, sort_order
        ("root", None, "chan1", "topic", "Root Topic", "The root", "root_cid", True, 1.0),
        ("sub1", "root", "chan1", "topic", "Subtopic 1", "First sub", "sub1_cid", True, 1.0),
        ("vid1", "sub1", "chan1", "video", "Video 1", "A video", "vid1_cid", True, 1.0),
        ("vid2", "sub1", "chan1", "video", "Video 2", "Another video", "vid2_cid", True, 2.0),
    ]
    
    cursor.executemany("""
        INSERT INTO content_contentnode 
        (id, parent_id, channel_id, kind, title, description, content_id, available, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, nodes)
    
    conn.commit()
    conn.close()
    return db_path

@pytest.fixture
def kuzu_db(tmp_path: Path) -> kuzu.Database:
    db_path = tmp_path / "kuzu_test"
    return kuzu.Database(str(db_path))

def test_kolibri_topic_extractor(mock_kolibri_db: Path, kuzu_db: kuzu.Database) -> None:
    conn = kuzu.Connection(kuzu_db)
    extractor = KolibriTopicExtractor(str(mock_kolibri_db), conn)
    
    # Run extraction
    extractor.extract_and_load()
    
    # Verify ContentNode vertices
    result = conn.execute("MATCH (n:ContentNode) RETURN n.id, n.title, n.kind ORDER BY n.id")
    rows = []
    while result.has_next():
        rows.append(result.get_next())
    
    assert len(rows) == 4
    assert rows[0][0] == "root"
    assert rows[0][1] == "Root Topic"
    assert rows[0][2] == "topic"
    
    # Verify Parent-Child relationships
    result = conn.execute("MATCH (p:ContentNode)-[:HAS_CHILD]->(c:ContentNode) RETURN p.id, c.id")
    rels = []
    while result.has_next():
        rels.append(result.get_next())
    
    assert len(rels) == 3
    # Check if (root, sub1), (sub1, vid1), (sub1, vid2) exist
    rel_set = set((r[0], r[1]) for r in rels)
    assert ("root", "sub1") in rel_set
    assert ("sub1", "vid1") in rel_set
    assert ("sub1", "vid2") in rel_set
