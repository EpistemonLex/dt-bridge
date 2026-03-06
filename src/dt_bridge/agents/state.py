from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    """
    The state of the LangGraph multi-agent system.
    """
    # The current user query or lesson objective
    objective: str
    
    # Context retrieved from Kolibri/LanceDB
    context: Annotated[List[str], operator.add]
    
    # Cognitive assessment of the student
    student_profile: dict
    
    # The generated lesson plan or output
    output: dict
    
    # Tracking which agents have run
    history: Annotated[List[str], operator.add]
