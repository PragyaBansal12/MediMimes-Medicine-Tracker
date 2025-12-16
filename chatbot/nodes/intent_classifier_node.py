from chatbot.state import State
from chatbot.llm import llm
import json
import re
import logging

logger = logging.getLogger(__name__)


INTENT_CLASSIFIER_PROMPT = """
You are an intent classification module for a medication adherence assistant.
Your ONLY job is to classify the user's message into a safe, predefined intent.

Return a JSON dictionary ONLY, with these keys:

{
  "intent": "<one of: symptom_logging | medication_query | adherence_conversation | db_query | health_education | smalltalk | fallback>",
  "query_type": "<string or null>"
}

INTENT RULES:
-------------------------------------
1. symptom_logging  
   User reports symptoms:
   "I feel dizzy", "I have nausea", "I have a headache"

2. medication_query  
   Asking what a medication does:
   "What is metformin?", "What is aspirin used for?", "Tell me about ibuprofen"

3. adherence_conversation  
   Talking about missed/taken doses:
   "I missed my dose", "I took my medicine already", "I forgot to take my pills"

4. db_query  
   User asks about their OWN medication history:
   - "Did I take my medicine yesterday?"
   - "What is my schedule today?"
   - "Show me my medication schedule"
   - "What medications am I taking?"

   For db_query, you MUST also set query_type to one of:
   "last_missed_dose", "today_schedule", "weekly_summary",
   "dose_taken_yesterday", "recent_history", "upcoming_doses"

   Examples:
   - "Did I take my medicine yesterday?" → query_type: "dose_taken_yesterday"
   - "What's my schedule today?" → query_type: "today_schedule"
   - "Show me my recent doses" → query_type: "recent_history"
   - "What are my upcoming doses?" → query_type: "upcoming_doses"

5. health_education
   General medical knowledge questions:
   "What is hypertension?", "Why is sleep important?"

6. smalltalk
   Greetings, jokes:
   "Hi", "How are you?", "Hello"

7. fallback
   If unclear or doesn't fit above categories.

CONSTRAINTS:
-------------------------------------
- NEVER diagnose.
- NEVER recommend any medical changes.
- Return ONLY JSON.
- If unsure → intent = "fallback"

EXAMPLES:
-------------------------------------
Input: "Did I take my medicine yesterday?"
Output: {"intent": "db_query", "query_type": "dose_taken_yesterday"}

Input: "What is aspirin?"
Output: {"intent": "medication_query", "query_type": null}

Input: "I have a headache"
Output: {"intent": "symptom_logging", "query_type": null}

Input: "What's my schedule today?"
Output: {"intent": "db_query", "query_type": "today_schedule"}
"""


def intent_classifier_node(state: State):
    """
    Classifies user intent and routes to appropriate domain node.
    
    Returns:
        State with intent, query_type, and route fields populated
    """
    user_input = state["user_input"]

    # Build prompt
    prompt = INTENT_CLASSIFIER_PROMPT + f"\n\nUser message:\n{user_input}\n\nReturn ONLY the JSON object, nothing else."

    # Call the LLM
    try:
        raw = llm.invoke(prompt)
        
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        state["intent"] = "fallback"
        state["query_type"] = None
        state["route"] = "response_generation_node"
        return state

    # Extract JSON from LLM output
    data = None
    
    try:
        # Strategy 1: Check if raw is already a dict
        if isinstance(raw, dict):
            data = raw
        
        # Strategy 2: Check if it has .content attribute (LangChain messages)
        elif hasattr(raw, 'content'):
            text = raw.content
            
            # Try direct JSON parse
            try:
                data = json.loads(text)
            except:
                # Try to extract JSON with regex
                match = re.search(r'\{[\s\S]*?\}', text)
                if match:
                    data = json.loads(match.group())
        
        # Strategy 3: Convert to string and search
        else:
            text = str(raw)
            
            try:
                data = json.loads(text)
            except:
                match = re.search(r'\{[\s\S]*?\}', text)
                if match:
                    data = json.loads(match.group())
        
        # If still no data, use fallback
        if data is None:
            logger.warning("Could not parse intent from LLM response")
            data = {"intent": "fallback", "query_type": None}
            
    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        data = {"intent": "fallback", "query_type": None}

    # Sanitize intent
    allowed_intents = {
        "symptom_logging",
        "medication_query",
        "adherence_conversation",
        "db_query",
        "health_education",
        "smalltalk",
        "fallback",
    }

    intent = data.get("intent")
    query_type = data.get("query_type")

    if intent not in allowed_intents:
        logger.warning(f"Invalid intent '{intent}', using fallback")
        intent = "fallback"
        query_type = None

    # Route selection
    route_map = {
        "symptom_logging": "symptom_node",
        "medication_query": "medication_rag_node",
        "adherence_conversation": "adherence_node",
        "db_query": "db_query_node",
        "health_education": "education_node",
        "smalltalk": "response_generation_node",
        "fallback": "response_generation_node",
    }

    # Write to state
    state["intent"] = intent
    state["query_type"] = query_type
    state["route"] = route_map[intent]

    return state