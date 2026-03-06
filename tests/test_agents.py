import pytest
from langgraph.graph import StateGraph, END
from dt_bridge.agents.state import AgentState
from dt_bridge.agents.librarian import LibrarianNode
from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer
import lancedb
import pandas as pd
from pathlib import Path

@pytest.fixture
def mock_vectorizer(tmp_path: Path) -> TranscriptVectorizer:
    lancedb_dir = tmp_path / "lancedb"
    vectorizer = TranscriptVectorizer(str(tmp_path), str(lancedb_dir))
    
    # Create some mock data with a vector column
    import numpy as np
    df = pd.DataFrame([
        {
            "id": "v1_0", 
            "node_id": "v1", 
            "text": "Gravity is the force that pulls objects toward each other.", 
            "checksum": "abc",
            "vector": np.random.rand(128).astype(np.float32)
        },
        {
            "id": "v1_1", 
            "node_id": "v1", 
            "text": "Sir Isaac Newton formulated the universal law of gravitation.", 
            "checksum": "abc",
            "vector": np.random.rand(128).astype(np.float32)
        }
    ])
    vectorizer.db.create_table("transcripts", data=df)
    return vectorizer

from unittest.mock import MagicMock

def test_librarian_node(mock_vectorizer: TranscriptVectorizer) -> None:
    # Mock the search method to avoid real vector search in tests
    mock_vectorizer.search = MagicMock(return_value=pd.DataFrame([
        {"text": "Gravity is the force that pulls objects toward each other."}
    ]))
    
    # Build a simple graph
    workflow = StateGraph(AgentState)
    
    librarian = LibrarianNode(mock_vectorizer)
    workflow.add_node("librarian", librarian)
    workflow.set_entry_point("librarian")
    workflow.add_edge("librarian", END)
    
    app = workflow.compile()
    
    # Initial state
    initial_state = {
        "objective": "gravitation",
        "context": [],
        "student_profile": {},
        "output": {},
        "history": []
    }
    
    # Run the graph
    # Note: Search without embeddings will do a scan/keyword search if configured
    # In LanceDB, if no vector is provided to search(), it will do a keyword search?
    # No, it usually requires a vector. 
    # But since we're in a test, let's see what happens.
    final_state = app.invoke(initial_state)
    
    assert "context" in final_state
    assert "history" in final_state
    assert any("Librarian:" in h for h in final_state["history"])
