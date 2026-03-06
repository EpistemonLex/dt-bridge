import os
import re
import lancedb
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path

class TranscriptVectorizer:
    """
    Extracts WebVTT transcripts from Kolibri storage, chunks them,
    and ingests them into LanceDB.
    """

    def __init__(
        self, 
        kolibri_content_dir: str, 
        lancedb_dir: str,
        table_name: str = "transcripts"
    ) -> None:
        self.content_dir = Path(kolibri_content_dir)
        self.db = lancedb.connect(lancedb_dir)
        self.table_name = table_name

    def _strip_vtt(self, vtt_content: str) -> str:
        """Strip timestamps and metadata from VTT content."""
        # Simple regex to remove timestamps like 00:00:00.000 --> 00:00:00.000
        # Also remove WEBVTT header
        lines = vtt_content.splitlines()
        clean_lines = []
        for line in lines:
            if "-->" in line or line.startswith("WEBVTT") or not line.strip():
                continue
            # Remove HTML tags if any (e.g. <c.color>...)
            line = re.sub(r'<[^>]*>', '', line)
            clean_lines.append(line.strip())
        return " ".join(clean_lines)

    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Split text into chunks of roughly chunk_size words with overlap."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    def process_transcripts(self, file_data: List[Dict[str, Any]]) -> None:
        """
        Processes a list of file metadata (id, checksum, node_id) 
        and ingests their transcripts into LanceDB.
        """
        all_chunks = []
        for item in file_data:
            checksum = item['checksum']
            node_id = item['node_id']
            
            # Construct path: storage/c1/c2/checksum.vtt
            vtt_path = self.content_dir / "storage" / checksum[0] / checksum[1] / f"{checksum}.vtt"
            
            if not vtt_path.exists():
                continue
            
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            clean_text = self._strip_vtt(content)
            chunks = self._chunk_text(clean_text)
            
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "id": f"{node_id}_{i}",
                    "node_id": node_id,
                    "text": chunk,
                    "checksum": checksum
                })
        
        if not all_chunks:
            return

        df = pd.DataFrame(all_chunks)
        
        # In a real scenario, we'd use an embedding function here.
        # LanceDB can handle embedding automatically if a model is provided.
        # For now, we'll assume the table will be created with an embedding function 
        # or we'll just store the text for now.
        if self.table_name in self.db.list_tables().tables:
            self.db[self.table_name].add(df)
        else:
            # We'll need a default embedding function if we want search to work later.
            # Using lancedb.embeddings.get_registry().get("sentence-transformers").create()
            # but we'll keep it simple for now to avoid downloading models in a test.
            self.db.create_table(self.table_name, data=df)

    def search(self, query: str, limit: int = 5) -> pd.DataFrame:
        """Search for relevant transcripts."""
        table = self.db[self.table_name]
        return table.search(query).limit(limit).to_pandas()
