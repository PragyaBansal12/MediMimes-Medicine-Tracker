from chatbot.state import State


# ----------------emrgency node----------------------

def emergency_node(state: State):

    emergency_type = state.get("emergency_type")

    message = (
        "This may be a medical emergency. Please seek immediate medical help or "
        "contact your local emergency services right now."
    )


    TEMPLATES = {
        "cardiac_emergency": (
            "Chest pain or severe chest discomfort can be serious. "
            "Please seek emergency medical help immediately or call your local "
            "emergency services."
        ),

        "respiratory_distress": (
            "Difficulty breathing can be life-threatening. "
            "Please seek immediate medical help or call emergency services now."
        ),

        "possible_overdose": (
            "Taking more medication than prescribed can be dangerous. "
            "Please contact emergency medical services or go to the nearest hospital immediately."
        ),

        "severe_allergic_reaction": (
            "Signs of a severe allergic reaction can be life-threatening. "
            "Please seek urgent medical attention or call emergency services."
        ),

        "mental_health_crisis": (
            "I'm really sorry that you're feeling this way. You deserve immediate support. "
            "Please reach out to a trusted person, and contact emergency services or a local suicide prevention helpline right now."
        ),

        "acute_critical_symptom": (
            "The symptoms you're describing could be serious. "
            "Please seek urgent medical attention or contact emergency services immediately."
        )
    }

    if emergency_type in TEMPLATES:
        message = TEMPLATES[emergency_type]

    state["response"]=message
    # State["route"]=None
    return state
    
