from typing import TypedDict, Optional, Dict, List, Any

class State(TypedDict, total=False):
    # ----------------------------------------------------
    # Backend Inputs
    # ----------------------------------------------------
    user_id: int                   # Authenticated Django user
    user_input: str                # Raw user message
    conversation_history: List[Dict[str, str]]  # NEW: Previous 5 message pairs

    # ----------------------------------------------------
    # Safety Gate
    # ----------------------------------------------------
    is_emergency: bool             # True if red-flagged
    emergency_type: Optional[str]  # "chest_pain", "overdose", etc.

    # ----------------------------------------------------
    # Intent Classification
    # ----------------------------------------------------
    intent: Optional[str]          # medication / symptom / db_query / education / adherence / smalltalk
    query_type: Optional[str]      # Only for db_query intents

    # ----------------------------------------------------
    # Node Outputs (Structured Data)
    # ----------------------------------------------------
    medication_context: Optional[Dict[str, Any]]  # RAG output
    symptom_logs: Optional[List[Dict[str, Any]]]  # In-session only
    education_content: Optional[str]              # Education node output
    db_query_result: Optional[Dict[str, Any]]     # SQL results (structured)
    adherence_summary: Optional[Dict[str, Any]]   # For adherence conversation
    behavior_signal: Optional[str]                # Motivation tag ("mild", "struggle")

    # ----------------------------------------------------
    # Final Output
    # ----------------------------------------------------
    response: Optional[str]         # Final message from response generator

