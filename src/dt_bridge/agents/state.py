"""State definitions for the LangGraph agent roundtable."""

import operator
from typing import Annotated, TypedDict

from dt_contracts.lesson_plan import HybridLessonPlan
from dt_contracts.telemetry import TelemetryLog


class AgentState(TypedDict):
    """The state of the LangGraph multi-agent system."""

    # The current user query or lesson objective
    objective: str

    # Context retrieved from Kolibri/LanceDB
    context: Annotated[list[str], operator.add]

    # Raw telemetry synced from the student device
    telemetry: list[TelemetryLog]

    # Internal reasoning and logs
    history: Annotated[list[str], operator.add]

    # The final generated payload
    output: HybridLessonPlan | None
