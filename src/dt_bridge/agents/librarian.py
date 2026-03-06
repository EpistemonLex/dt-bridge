"""Librarian agent node for LangGraph."""


from dt_bridge.agents.state import AgentState
from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer


class LibrarianNode:
    """LangGraph node for the Librarian agent.

    Responsible for querying LanceDB for pedagogical context.
    """

    def __init__(self, vectorizer: TranscriptVectorizer) -> None:
        """Initialize the Librarian node.

        :param vectorizer: The TranscriptVectorizer instance to use.
        """
        self.vectorizer = vectorizer

    def __call__(self, state: AgentState) -> dict[str, list[str]]:
        """Execute the Librarian agent's retrieval.

        :param state: The current AgentState.
        :return: A partial update to the state with context and history.
        """
        objective = state.get("objective", "")
        if not objective:
            return {"history": ["Librarian: No objective provided, skipped retrieval."]}

        # Retrieve context from LanceDB
        results = self.vectorizer.search(objective, limit=3)

        context_chunks: list[str] = []
        if not results.empty:
            for _, row in results.iterrows():
                # Ensure we cast to string to be safe
                text = str(row["text"])
                context_chunks.append(text)

        return {
            "context": context_chunks,
            "history": [
                f"Librarian: Retrieved {len(context_chunks)} context chunks for '{objective}'.",
            ],
        }
