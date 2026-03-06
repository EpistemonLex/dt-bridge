from typing import Any, Dict
from dt_bridge.agents.state import AgentState
from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer

class LibrarianNode:
    """
    LangGraph node for the Librarian agent.
    Responsible for querying LanceDB for pedagogical context.
    """

    def __init__(self, vectorizer: TranscriptVectorizer) -> None:
        self.vectorizer = vectorizer

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        """Execute the Librarian agent's retrieval."""
        objective = state.get("objective", "")
        if not objective:
            return {"history": ["Librarian: No objective provided, skipped retrieval."]}
        
        # Retrieve context from LanceDB
        # In a real scenario, this would use embeddings
        results = self.vectorizer.search(objective, limit=3)
        
        context_chunks = []
        if not results.empty:
            for _, row in results.iterrows():
                context_chunks.append(row["text"])
        
        return {
            "context": context_chunks,
            "history": [f"Librarian: Retrieved {len(context_chunks)} context chunks for '{objective}'."]
        }
