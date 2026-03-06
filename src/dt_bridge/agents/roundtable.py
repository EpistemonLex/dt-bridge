"""Roundtable orchestrator for Deepthought agents."""

from langgraph.graph import END, StateGraph

from dt_bridge.agents.assessor import AssessorNode
from dt_bridge.agents.foreman import ForemanNode
from dt_bridge.agents.librarian import LibrarianNode
from dt_bridge.agents.state import AgentState
from dt_bridge.etl.transcript_vectorizer import TranscriptVectorizer


def create_roundtable(vectorizer: TranscriptVectorizer) -> StateGraph[AgentState]:
    """Create the Roundtable multi-agent graph.

    :param vectorizer: The TranscriptVectorizer for the Librarian.
    :return: An uncompiled StateGraph.
    """
    workflow: StateGraph[AgentState] = StateGraph(AgentState)

    # Initialize nodes
    librarian = LibrarianNode(vectorizer)
    assessor = AssessorNode()
    foreman = ForemanNode()

    # Add nodes to graph
    workflow.add_node("librarian", librarian)
    workflow.add_node("assessor", assessor)
    workflow.add_node("foreman", foreman)

    # Define edges (Sequential for now)
    workflow.set_entry_point("librarian")
    workflow.add_edge("librarian", "assessor")
    workflow.add_edge("assessor", "foreman")
    workflow.add_edge("foreman", END)

    return workflow
