"""Test suite for dt-bridge agents."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from langgraph.graph import END, StateGraph

from dt_bridge.agents.librarian import LibrarianNode
from dt_bridge.agents.state import AgentState
from dt_bridge.etl.transcript_vectorizer import KolibriFileMetadata, TranscriptVectorizer


@pytest.fixture
def mock_vectorizer(tmp_path: Path) -> TranscriptVectorizer:
    """Create a mock TranscriptVectorizer."""
    lancedb_dir = tmp_path / "lancedb"
    vectorizer = TranscriptVectorizer(str(tmp_path), str(lancedb_dir))

    # Create some mock data with a vector column
    rng = np.random.default_rng()
    df = pd.DataFrame(
        [
            {
                "id": "v1_0",
                "node_id": "v1",
                "text": "Gravity is the force that pulls objects toward each other.",
                "checksum": "abc",
                "vector": rng.random(128).astype(np.float32),
            },
            {
                "id": "v1_1",
                "node_id": "v1",
                "text": "Sir Isaac Newton formulated the universal law of gravitation.",
                "checksum": "abc",
                "vector": rng.random(128).astype(np.float32),
            },
        ],
    )
    vectorizer.db.create_table("transcripts", data=df)
    return vectorizer


def test_librarian_node(mock_vectorizer: TranscriptVectorizer) -> None:
    """Test the Librarian agent node."""
    # Build a simple graph
    workflow = StateGraph(AgentState)

    librarian = LibrarianNode(mock_vectorizer)
    workflow.add_node("librarian", librarian)
    workflow.set_entry_point("librarian")
    workflow.add_edge("librarian", END)

    app = workflow.compile()

    # Initial state
    initial_state: AgentState = {
        "objective": "gravitation",
        "context": [],
        "student_profile": {
            "node_id": "vid1",
            "mastery_score": 0.0,
            "struggles": [],
            "last_sync": "2026-03-06",
        },
        "output": {"plan_id": "p1", "nodes": [], "config": {}},
        "history": [],
    }

    # Patch the search method to avoid real vector search in tests
    with patch.object(
        mock_vectorizer,
        "search",
        return_value=pd.DataFrame(
            [{"text": "Gravity is the force that pulls objects toward each other."}],
        ),
    ):
        # Run the graph
        # cast to satisfy complex StateT binding in langgraph
        invoke_result = app.invoke(cast("Any", initial_state))  # architectural: allowed-object (Satisfy langgraph Pregel.invoke type hint)
        final_state = cast("AgentState", invoke_result)

    assert "context" in final_state
    assert "history" in final_state
    assert any("Librarian:" in h for h in final_state["history"])


def test_librarian_node_empty_objective(mock_vectorizer: TranscriptVectorizer) -> None:
    """Test Librarian node with empty objective."""
    workflow = StateGraph(AgentState)
    librarian = LibrarianNode(mock_vectorizer)
    workflow.add_node("librarian", librarian)
    workflow.set_entry_point("librarian")
    workflow.add_edge("librarian", END)
    app = workflow.compile()

    initial_state: AgentState = {
        "objective": "",
        "context": [],
        "student_profile": {
            "node_id": "vid1",
            "mastery_score": 0.0,
            "struggles": [],
            "last_sync": "2026-03-06",
        },
        "output": {"plan_id": "p1", "nodes": [], "config": {}},
        "history": [],
    }

    invoke_result = app.invoke(cast("Any", initial_state))  # architectural: allowed-object
    final_state = cast("AgentState", invoke_result)

    assert not final_state["context"]
    assert any("skipped retrieval" in h for h in final_state["history"])


def test_transcript_vectorizer_metadata_type(
    mock_kolibri_content: Path, tmp_path: Path,
) -> None:
    """Test that process_transcripts accepts KolibriFileMetadata."""
    lancedb_dir = tmp_path / "lancedb"
    vectorizer = TranscriptVectorizer(str(mock_kolibri_content), str(lancedb_dir))

    # This should satisfy mypy
    file_data: list[KolibriFileMetadata] = [
        {"id": "file1", "checksum": "abcd123", "node_id": "vid1"},
    ]

    vectorizer.process_transcripts(file_data)
    assert "transcripts" in vectorizer.db.list_tables().tables
