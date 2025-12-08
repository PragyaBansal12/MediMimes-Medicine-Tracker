# imports
from chatbot.state import State
from datetime import datetime

# -----------red flag node--------------

def red_flag_node(State):
    text = State["user_input"].lower()

    #Helper to set emergency flags
    def flag(emergency_type):
        State["is_emergency"] = True
        State["emergency_type"] = emergency_type
        State["route"] = "emergency_node"
        return State

    # 1. Hard emergency signals
    EMERGENCY_SIGNS = {
        "chest pain": "cardiac_emergency",
        "severe chest pain": "cardiac_emergency",
        "difficulty breathing": "respiratory_distress",
        "can't breathe": "respiratory_distress",
        "shortness of breath": "respiratory_distress",
        "trouble breathing": "respiratory_distress",
        "fainted": "loss_of_consciousness",
        "unconscious": "loss_of_consciousness",
        "not waking up": "loss_of_consciousness",
        "kill ": "mental_health_crisis",
        "end my life": "mental_health_crisis",
        "hurt myself": "mental_health_crisis",  
        "suicide": "mental_health_crisis",
    }

    for phrase, tag in EMERGENCY_SIGNS.items():
        if phrase in text:
            return flag(tag)

    # 2. Overdose indicators
    OVERDOSE_TERMS = [
        "took double dose",
        "took too many pills",
        "overdose",
        "accidentally took extra",
        "took two pills instead of one",
        "took more than prescribed",
    ]

    for term in OVERDOSE_TERMS:
        if term in text:
            return flag("possible_overdose")

    # 3. Severe allergic reactions
    ALLERGY_TERMS = [
        "swelling of face",
        "swelling of lips",
        "swelling of tongue",
        "swelling of throat",
        "can't swallow",
        "tightness in throat",
        "hives and trouble breathing",
        "skin turning blue",
    ]

    for term in ALLERGY_TERMS:
        if term in text:
            return flag("severe_allergic_reaction")

    # 4. Suicide / self harm
    SUICIDE_TERMS = [
        "want to die",
        "end my life",
        "i don't want to live",
        "hurt myself",
        "kill myself",
    ]

    for term in SUICIDE_TERMS:
        if term in text:
            return flag("mental_health_crisis")

    # 5. Severe acute symptoms
    ACUTE_TERMS = [
        "vomiting blood",
        "blood in vomit",
        "blood in stool",
        "vision loss",
        "seizure",
        "fit",
        "convulsion",
        "can't move arm",
        "can't move leg",
        "slurred speech",
    ]

    for term in ACUTE_TERMS:
        if term in text:
            return flag("acute_critical_symptom")

   
    State["is_emergency"] = False
    State["emergency_type"] = None
    State["route"] = "intent_classifier_node"
    return State
