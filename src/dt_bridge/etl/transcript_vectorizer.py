"""Transcript extraction and LanceDB vectorization."""

import re
from pathlib import Path
from typing import TypedDict, cast

import lancedb
import pandas as pd


class KolibriFileMetadata(TypedDict):
    """Metadata for a Kolibri content file."""

    id: str
    checksum: str
    node_id: str


class TranscriptChunk(TypedDict):
    """A chunk of transcript text stored in LanceDB."""

    id: str
    node_id: str
    text: str
    checksum: str


class TranscriptVectorizer:
    """Extracts WebVTT transcripts from Kolibri storage, chunks them.

    Ingests them into LanceDB.
    """

    def __init__(
        self, kolibri_content_dir: str, lancedb_dir: str, table_name: str = "transcripts",
    ) -> None:
        """Initialize the vectorizer.

        :param kolibri_content_dir: Path to Kolibri content storage.
        :param lancedb_dir: Path to LanceDB storage.
        :param table_name: Name of the table in LanceDB.
        """
        self.content_dir = Path(kolibri_content_dir)
        self.db = lancedb.connect(lancedb_dir)
        self.table_name = table_name

    def _strip_vtt(self, vtt_content: str) -> str:
        """Strip timestamps and metadata from VTT content.

        :param vtt_content: Raw VTT string.
        :return: Cleaned text.
        """
        # Simple regex to remove timestamps like 00:00:00.000 --> 00:00:00.000
        # Also remove WEBVTT header
        lines = vtt_content.splitlines()
        clean_lines = []
        for raw_line in lines:
            if "-->" in raw_line or raw_line.startswith("WEBVTT") or not raw_line.strip():
                continue
            # Remove HTML tags if any (e.g. <c.color>...)
            clean_line = re.sub(r"<[^>]*>", "", raw_line)
            clean_lines.append(clean_line.strip())
        return " ".join(clean_lines)

    def _chunk_text(
        self, text: str, chunk_size: int = 300, overlap: int = 50,
    ) -> list[str]:
        """Split text into chunks of roughly chunk_size words with overlap.

        :param text: Cleaned transcript text.
        :param chunk_size: Number of words per chunk.
        :param overlap: Number of words to overlap between chunks.
        :return: List of text chunks.
        """
        words = text.split()
        chunks: list[str] = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    def process_transcripts(self, file_data: list[KolibriFileMetadata]) -> None:
        """Process a list of file metadata and ingest transcripts into LanceDB.

        :param file_data: List of KolibriFileMetadata objects.
        """
        all_chunks: list[TranscriptChunk] = []
        for item in file_data:
            checksum = str(item["checksum"])
            node_id = str(item["node_id"])

            # Construct path: storage/c1/c2/checksum.vtt
            vtt_path = (
                self.content_dir
                / "storage"
                / checksum[0]
                / checksum[1]
                / f"{checksum}.vtt"
            )

            if not vtt_path.exists():
                continue

            with vtt_path.open(encoding="utf-8") as f:
                content = f.read()

            clean_text = self._strip_vtt(content)
            chunks = self._chunk_text(clean_text)

            for i, chunk in enumerate(chunks):
                all_chunks.append(
                    {
                        "id": f"{node_id}_{i}",
                        "node_id": node_id,
                        "text": str(chunk),
                        "checksum": checksum,
                    },
                )

        if not all_chunks:
            return

        df = pd.DataFrame(all_chunks)

        if self.table_name in self.db.list_tables().tables:
            self.db[self.table_name].add(df)
        else:
            self.db.create_table(self.table_name, data=df)

    def search(self, query: str, limit: int = 5) -> pd.DataFrame:
        """Search for relevant transcripts.

        :param query: Search query string.
        :param limit: Maximum number of results.
        :return: DataFrame of results.
        """
        table = self.db[self.table_name]
        return cast("pd.DataFrame", table.search(query).limit(limit).to_pandas())
