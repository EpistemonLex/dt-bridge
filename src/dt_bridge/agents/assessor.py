"""Assessor agent node for LangGraph."""


from dt_contracts.telemetry import ActionType

from dt_bridge.agents.state import AgentState

ERROR_THRESHOLD = 3


class AssessorNode:
    """LangGraph node for the Assessor agent.

    Analyzes student telemetry to determine cognitive gaps.
    """

    def __call__(self, state: AgentState) -> dict[str, list[str]]:
        """Execute the Assessor agent's analysis.

        :param state: The current AgentState.
        :return: A partial update to the state history.
        """
        telemetry = state.get("telemetry", [])
        if not telemetry:
            return {"history": ["Assessor: No telemetry available, assuming baseline proficiency."]}

        # Simple analysis: count compilation errors
        errors = [log for log in telemetry if log.action_type == ActionType.COMPILATION_ERROR]

        if len(errors) > ERROR_THRESHOLD:
            gap_summary = f"Assessor: Detected {len(errors)} compilation errors. High friction in creation phase."
        else:
            gap_summary = f"Assessor: Student is operating with low friction ({len(errors)} errors)."

        return {
            "history": [gap_summary],
        }
