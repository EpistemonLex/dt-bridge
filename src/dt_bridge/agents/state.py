"""State definitions for the LangGraph agent roundtable."""

import operator
from typing import Annotated, TypedDict


class StudentProfile(TypedDict):
    """Represents the cognitive assessment of a student."""

    node_id: str
    mastery_score: float
    struggles: list[str]
    last_sync: str


class LessonPlan(TypedDict):
    """Represents a generated HybridLessonPlan payload."""

    plan_id: str
    nodes: list[str]
    config: dict[str, str]


class AgentState(TypedDict):
    """The state of the LangGraph multi-agent system."""

    # The current user query or lesson objective
    objective: str

    # Context retrieved from Kolibri/LanceDB
    context: Annotated[list[str], operator.add]

    # Cognitive assessment of the student
    student_profile: StudentProfile

    # The generated lesson plan or output
    output: LessonPlan

    # Tracking which agents have run
    history: Annotated[list[str], operator.add]
