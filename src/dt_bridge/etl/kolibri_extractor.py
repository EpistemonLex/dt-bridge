import sqlite3
import kuzu
from typing import Optional, List, Tuple

class KolibriTopicExtractor:
    """
    Extracts Kolibri ContentNode hierarchy from a channel SQLite database
    and maps it into a KuzuDB graph.
    """

    def __init__(self, kolibri_db_path: str, kuzu_conn: kuzu.Connection) -> None:
        self.kolibri_db_path = kolibri_db_path
        self.kuzu_conn = kuzu_conn
        self._setup_kuzu_schema()

    def _setup_kuzu_schema(self) -> None:
        """Initialize the KuzuDB schema for ContentNodes."""
        try:
            self.kuzu_conn.execute(
                "CREATE NODE TABLE ContentNode(id STRING, title STRING, kind STRING, "
                "description STRING, channel_id STRING, content_id STRING, PRIMARY KEY(id))"
            )
        except Exception as e:
            # Table might already exist
            if "already exists" not in str(e).lower():
                raise

        try:
            self.kuzu_conn.execute(
                "CREATE REL TABLE HAS_CHILD(FROM ContentNode TO ContentNode)"
            )
        except Exception as e:
            # Table might already exist
            if "already exists" not in str(e).lower():
                raise

    def extract_and_load(self) -> None:
        """Execute the extraction and loading process."""
        import pandas as pd
        conn = sqlite3.connect(self.kolibri_db_path)
        
        # Query all relevant ContentNodes
        df = pd.read_sql_query("""
            SELECT id, title, kind, description, channel_id, content_id, parent_id
            FROM content_contentnode
            WHERE available = 1
        """, conn)
        conn.close()

        if df.empty:
            return

        # Ensure all columns are strings and handle nulls
        for col in ['id', 'title', 'kind', 'description', 'channel_id', 'content_id']:
            df[col] = df[col].fillna("").astype(str)

        # Phase 1: Load all vertices
        import tempfile
        import os
        nodes_df = df[['id', 'title', 'kind', 'description', 'channel_id', 'content_id']]
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            nodes_df.to_parquet(tmp.name)
            tmp_path = tmp.name
        try:
            self.kuzu_conn.execute(f"COPY ContentNode FROM '{tmp_path}'")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Phase 2: Create all relationships
        rels_df = df[df['parent_id'].notna()][['parent_id', 'id']]
        rels_df.columns = ['from', 'to']
        if not rels_df.empty:
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                rels_df.to_parquet(tmp.name)
                tmp_path = tmp.name
            try:
                self.kuzu_conn.execute(f"COPY HAS_CHILD FROM '{tmp_path}'")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
