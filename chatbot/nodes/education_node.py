from chatbot.state import State
from chatbot.llm import llm


# --------------Education node------------
HEALTH_EDUCATION_PROMPT = """
You are a neutral, factual health education assistant.

Your job:
- Explain general health, conditions, medications, or physiology in simple terms.
- Speak in GENERAL terms, not about the specific user.
- Do NOT diagnose.
- Do NOT give treatment recommendations.
- Do NOT suggest dose changes or specific drugs.
- Do NOT tell the user what they personally should do.
- Avoid fear-inducing language or worst-case dramatization.
- You may explain potential risks in a calm, high-level way, without saying they WILL happen.

Always:
- Use "in general", "people", "many patients", etc., instead of "you".
- Keep the explanation concise and focused.
- At the end, add: 
  "For personal medical advice or decisions, it's important to consult a healthcare professional."

Now, based on the user's question, provide a clear, short educational explanation.
"""


# ---------------------------------------------------------
# HEALTH EDUCATION NODE
# ---------------------------------------------------------

def education_node(State: State):
    """
    Health Education Node:
    - Takes a general health/education question (already classified by intent node).
    - Uses LLM to generate a safe, non-diagnostic educational explanation.
    - Stores explanation in `education_content` for the final response generation node.
    - Does NOT directly produce the final chat response.
    """

    user_text = State["user_input"]

    # 1. Build prompt for LLM
    prompt = HEALTH_EDUCATION_PROMPT + "\n\nUser question:\n" + user_text

    # 2. Call LLM 
    try:
        explanation = llm.invoke(prompt)
        if isinstance(explanation, dict):
            # If your LLM wrapper returns structured output, adapt this as needed.
            explanation_text = explanation.get("text", "") or str(explanation)
        else:
            explanation_text = str(explanation)
    except Exception:
        # Fallback message if LLM call fails
        explanation_text = (
            "I’m unable to provide detailed information right now. "
            "For questions about health and medications, it's best to consult a healthcare professional."
        )

    # 3. Return partial state update
    # Final Response Generator Node will combine this with other context and send to user.

    State["education_content"]= explanation_text
    # State[ "route"]= "response_generation_node"
    
    return State
    