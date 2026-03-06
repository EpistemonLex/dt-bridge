"""Kolibri Retrieval Service (The Librarian)."""

from typing import TYPE_CHECKING, cast

import kuzu

if TYPE_CHECKING:
    from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer


class Librarian:
    """The Librarian provides a high-level interface to query the Kolibri.

    Knowledge Graph (KuzuDB) and Semantic Memory (LanceDB).
    """

    def __init__(self, kuzu_conn: kuzu.Connection, vectorizer: TranscriptVectorizer) -> None:
        """Initialize the Librarian.

        :param kuzu_conn: Connection to the Kolibri KuzuDB instance.
        :param vectorizer: Instance of TranscriptVectorizer for semantic search.
        """
        self.kuzu_conn = kuzu_conn
        self.vectorizer = vectorizer

    def _row_to_dict(self, result: kuzu.QueryResult, row: list[object]) -> dict[str, str]:
        """Convert a Kuzu row list to a dictionary using column names."""
        cols = result.get_column_names()
        return {str(cols[i]): str(row[i]) for i in range(len(cols))}

    def get_node_by_id(self, node_id: str) -> dict[str, str] | None:
        """Retrieve a single ContentNode by its ID.

        :param node_id: The Kolibri ID of the node.
        :return: A dictionary of node properties or None.
        """
        query = "MATCH (n:ContentNode {id: $id}) RETURN n.id, n.title, n.kind, n.description"
        query_result = self.kuzu_conn.execute(query, {"id": node_id})
        result = cast("kuzu.QueryResult", query_result)
        if result.has_next():
            row = cast("list[object]", result.get_next())
            # architectural: allowed-object (Kuzu row result)
            return self._row_to_dict(result, row)
        return None

    def get_children(self, parent_id: str) -> list[dict[str, str]]:
        """Retrieve all child nodes for a given parent node.

        :param parent_id: The ID of the parent node.
        :return: A list of child node properties.
        """
        query = (
            "MATCH (p:ContentNode {id: $id})-[:HAS_CHILD]->(c:ContentNode) "
            "RETURN c.id, c.title, c.kind, c.description"
        )
        query_result = self.kuzu_conn.execute(query, {"id": parent_id})
        result = cast("kuzu.QueryResult", query_result)
        children = []
        while result.has_next():
            row = cast("list[object]", result.get_next())
            # architectural: allowed-object (Kuzu row result)
            children.append(self._row_to_dict(result, row))
        return children

    def get_parent(self, child_id: str) -> dict[str, str] | None:
        """Retrieve the parent node for a given child node.

        :param child_id: The ID of the child node.
        :return: Properties of the parent node or None.
        """
        query = (
            "MATCH (p:ContentNode)-[:HAS_CHILD]->(c:ContentNode {id: $id}) "
            "RETURN p.id, p.title, p.kind, p.description"
        )
        query_result = self.kuzu_conn.execute(query, {"id": child_id})
        result = cast("kuzu.QueryResult", query_result)
        if result.has_next():
            row = cast("list[object]", result.get_next())
            # architectural: allowed-object (Kuzu row result)
            return self._row_to_dict(result, row)
        return None

    def semantic_search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """Search for relevant transcript chunks in LanceDB.

        :param query: The search query string.
        :param limit: Maximum number of results to return.
        :return: A list of transcript chunks with metadata.
        """
        df = self.vectorizer.search(query, limit=limit)
        results = []
        for _, row in df.iterrows():
            results.append({
                "text": str(row.get("text", "")),
                "node_id": str(row.get("node_id", "")),
                "checksum": str(row.get("checksum", "")),
            })
        return results

    def get_context_for_lesson(self, node_id: str) -> dict[str, object]:
        """Compile a full pedagogical context for a specific lesson node.

        Includes node metadata, hierarchy info, and relevant transcripts.

        :param node_id: The ID of the lesson node.
        :return: A comprehensive context dictionary.
        """
        node = self.get_node_by_id(node_id)
        if not node:
            return {}

        parent = self.get_parent(node_id)

        # If it's a video, get its specific transcripts
        # If it's a topic, get transcripts for its children?
        # For now, let's just search for the title
        transcripts = self.semantic_search(node.get("title", ""), limit=3)

        return {
            "node": node,
            "parent": parent,
            "transcripts": transcripts,
            # architectural: allowed-object (Comprehensive context dictionary)
        }
