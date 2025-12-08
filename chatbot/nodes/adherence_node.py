from chatbot.state import State
from datetime import datetime

# include the extracted in doctor appointmwent side later

# --------------------------Adherence Tracking Node --------------------------
# “I missed my dose today.”
# “I forgot last night’s medicine again.”
# “Did I take my pill today?”
# “I keep missing doses.”

from chatbot.state import State
from chatbot.llm import llm
from datetime import datetime
import json

ADHERENCE_EXTRACTION_PROMPT = """
Extract structured medication adherence information from the user's message.

Return ONLY a JSON object with this exact format:

{
  "event": "missed_dose" | "taken_dose" | "unsure",
  "dose_time": "morning" | "evening" | "night" | null,
  "date": "today" | "yesterday" | null,
  "reason": "<string or null>"
}

Rules:
- DO NOT diagnose.
- DO NOT give medical advice.
- Do not infer causes or consequences.
- Only extract what the user explicitly stated.
# - If uncertain, return "unsure".
"""

def adherence_node(state: State):

    user_text = state["user_input"]

    # -----------------------------
    # 1. Run extraction using LLM
    # -----------------------------
    raw = llm.invoke(
        ADHERENCE_EXTRACTION_PROMPT + "\nUser message: " + user_text
    )

    # Normalize
    try:
        parsed = raw if isinstance(raw, dict) else json.loads(raw)
    except:
        parsed = {
            "event": "unsure",
            "dose_time": None,
            "date": None,
            "reason": None
        }

    event = parsed.get("event", "unsure")
    dose_time = parsed.get("dose_time")
    date = parsed.get("date")
    reason = parsed.get("reason")

    # -----------------------------
    # 2. Create adherence summary object
    # -----------------------------
    adherence_summary = {
        "event": event,
        "dose_time": dose_time,
        "date": date,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }

    # -----------------------------
    # 3. Behavior signal for motivation
    # -----------------------------
    if event == "missed_dose":
        behavior_signal = f"missed_{dose_time or 'unknown'}"
    elif event == "taken_dose":
        behavior_signal = f"taken_{dose_time or 'unknown'}"
    else:
        behavior_signal = "adherence_unsure"

    # -----------------------------
    # 4. Write to state (only allowed fields)
    # -----------------------------
    state["adherence_summary"] = adherence_summary
    state["behavior_signal"] = behavior_signal

    # NO route modification
    # NO response generation
    return state
