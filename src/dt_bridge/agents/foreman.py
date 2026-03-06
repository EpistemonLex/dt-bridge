"""Foreman agent node for LangGraph."""


from dt_contracts.lesson_plan import (
    HybridLessonPlan,
    KolibriStep,
    SandboxEngine,
    SandboxStep,
    StepKind,
)

from dt_bridge.agents.state import AgentState


class ForemanNode:
    """LangGraph node for the Foreman agent.

    Generates the final HybridLessonPlan payload.
    """

    def __call__(self, state: AgentState) -> dict[str, list[str] | HybridLessonPlan]:
        """Execute the Foreman agent's payload generation.

        :param state: The current AgentState.
        :return: A partial update to the state with the final output.
        """
        objective = state.get("objective", "General Study")
        context = state.get("context", [])

        # Build steps
        steps: list[KolibriStep | SandboxStep] = []

        # Add a Kolibri step if we have context
        if context:
            steps.append(KolibriStep(
                kind=StepKind.KOLIBRI_CONSUMPTION,
                content_node_id="auto_node",
                channel_id="auto_channel",
                title=f"Basics of {objective}",
                transcript=context[0],
                key_vocabulary=[],
            ))

        # Add a Sandbox step (The creation phase)
        steps.append(SandboxStep(
            kind=StepKind.STEAM_SANDBOX,
            engine=SandboxEngine.KAPLAY,
            challenge_prompt=f"Apply your knowledge of {objective} in a coding sandbox.",
            initial_state={},
            validation_logic="assert True",
        ))

        plan = HybridLessonPlan(
            plan_id="plan_auto",
            student_id="student_auto",
            title=f"Lesson: {objective}",
            steps=steps,
            metadata={"source": "Roundtable Orchestrator"},
        )

        return {
            "output": plan,
            "history": ["Foreman: Generated HybridLessonPlan with 2 steps."],
        }
