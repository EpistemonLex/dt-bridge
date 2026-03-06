"""Common fixtures for dt-bridge tests."""

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def mock_kolibri_content(tmp_path: Path) -> Path:
    """Create mock Kolibri content storage."""
    storage_dir = tmp_path / "storage"
    # c1 = "a", c2 = "b", checksum = "abcd123"
    vtt_dir = storage_dir / "a" / "b"
    vtt_dir.mkdir(parents=True)
    vtt_file = vtt_dir / "abcd123.vtt"
    vtt_file.write_text("""WEBVTT

00:00:01.000 --> 00:00:05.000
This is a transcript about gravity.

00:00:06.000 --> 00:00:10.000
Gravity pulls objects together.
""")
    return tmp_path


@pytest.fixture
def mock_kolibri_db(tmp_path: Path) -> Path:
    """Create a mock Kolibri channel database."""
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

    cursor.executemany(
        """
        INSERT INTO content_contentnode
        (id, parent_id, channel_id, kind, title, description, content_id, available, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        nodes,
    )

    conn.commit()
    conn.close()
    return db_path
