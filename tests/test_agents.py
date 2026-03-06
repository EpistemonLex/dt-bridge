"""Test suite for dt-bridge agents."""

from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from dt_contracts.telemetry import ActionType, TelemetryLog
from langgraph.graph import END, StateGraph

from dt_bridge.agents.librarian import LibrarianNode
from dt_bridge.agents.roundtable import create_roundtable
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
        ],
    )
    vectorizer.db.create_table("transcripts", data=df)
    return vectorizer


def test_roundtable_full_flow(mock_vectorizer: TranscriptVectorizer) -> None:
    """Test the full Roundtable multi-agent flow."""
    workflow = create_roundtable(mock_vectorizer)
    app = workflow.compile()

    # Initial state with some telemetry
    initial_state: AgentState = {
        "objective": "gravitation",
        "context": [],
        "telemetry": [
            TelemetryLog(student_id="s1", action_type=ActionType.COMPILATION_ERROR, timestamp="2026-03-06T10:00:00", details={"err": "syntax"}),
            TelemetryLog(student_id="s1", action_type=ActionType.COMPILATION_ERROR, timestamp="2026-03-06T10:01:00", details={"err": "syntax"}),
            TelemetryLog(student_id="s1", action_type=ActionType.COMPILATION_ERROR, timestamp="2026-03-06T10:02:00", details={"err": "syntax"}),
            TelemetryLog(student_id="s1", action_type=ActionType.COMPILATION_ERROR, timestamp="2026-03-06T10:03:00", details={"err": "syntax"}),
        ],
        "history": [],
        "output": None,
    }

    # Patch the search method
    with patch.object(
        mock_vectorizer,
        "search",
        return_value=pd.DataFrame(
            [{"text": "Gravity is the force that pulls objects toward each other."}],
        ),
    ):
        invoke_result = app.invoke(cast("Any", initial_state))  # architectural: allowed-object (Satisfy langgraph Pregel.invoke type hint)
        final_state = cast("AgentState", invoke_result)

    assert len(final_state["context"]) > 0
    assert any("Assessor: Detected 4 compilation errors" in h for h in final_state["history"])
    assert any("Foreman: Generated HybridLessonPlan" in h for h in final_state["history"])
    assert final_state["output"] is not None
    assert final_state["output"].title == "Lesson: gravitation"
    assert len(final_state["output"].steps) == 2


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
        "telemetry": [],
        "output": None,
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
