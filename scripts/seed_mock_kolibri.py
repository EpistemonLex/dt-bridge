"""Seeding script for a minimal Kolibri mock database and transcripts."""

import sqlite3
from pathlib import Path


def seed() -> None:
    """Generate a minimal mock Kolibri database and VTT transcripts for ETL testing."""
    root_path = Path("dt-bridge/data")
    db_path = root_path / "african_storybook.sqlite3"
    content_dir = root_path / "kolibri_content"

    root_path.mkdir(parents=True, exist_ok=True)

    # 1. Seed SQLite Metadata
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE content_contentnode (
            id TEXT PRIMARY KEY,
            title TEXT,
            kind TEXT,
            description TEXT,
            channel_id TEXT,
            content_id TEXT,
            parent_id TEXT,
            available INTEGER
        )
    """)

    nodes = [
        ("root", "Ed-OS Core Curriculum", "topic", "Root", "ch1", "cid1", None, 1),
        ("physics", "Physics Foundation", "topic", "Intro", "ch1", "cid2", "root", 1),
        ("gravity", "Understanding Gravity", "video", "Gravity lesson", "ch1", "cid3", "physics", 1),
        ("math", "Early Mathematics", "topic", "Intro", "ch1", "cid4", "root", 1),
        ("fractions", "Learning Fractions", "exercise", "Fractions lesson", "ch1", "cid5", "math", 1),
    ]
    cursor.executemany("INSERT INTO content_contentnode VALUES (?, ?, ?, ?, ?, ?, ?, ?)", nodes)
    conn.commit()
    conn.close()
    print(f"✅ Mock Kolibri database seeded at {db_path}")

    # 2. Seed Mock Transcripts (.vtt)
    # We use hashes for checksums to match TranscriptVectorizer logic
    transcripts = [
        ("gravity_checksum", "gravity", "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nGravity is a fundamental force that pulls objects toward each other. On Earth, it keeps us on the ground."),
        ("fractions_checksum", "fractions", "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nA fraction represents a part of a whole. The numerator is the top number, and the denominator is the bottom."),
    ]

    for checksum, node_id, content in transcripts:
        # storage/c1/c2/checksum.vtt
        vtt_dir = content_dir / "storage" / checksum[0] / checksum[1]
        vtt_dir.mkdir(parents=True, exist_ok=True)
        vtt_path = vtt_dir / f"{checksum}.vtt"
        vtt_path.write_text(content, encoding="utf-8")
        print(f"✅ Seeded transcript for {node_id} at {vtt_path}")

if __name__ == "__main__":
    seed()
