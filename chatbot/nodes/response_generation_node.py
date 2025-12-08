from chatbot.state import State
from chatbot.llm import llm


# -----------------------respobnse generation node-------------------------
def response_generation_node(state):
    """
    Unified final message generator.
    All nodes pass structured information here.
    This node produces the ONLY user-facing message.
    
    Inputs it may receive:
      - state["education_content"]
      - state["db_query_result"]
      - state["medication_context"]
      - state["symptom_logs"]
      - state["adherence_summary"]
      - state["behavior_signal"]
      - state["intent"]
    
    Output:
      - {"response": "<final safe message>"}
    """

    intent = state.get("intent")
    education = state.get("education_content")
    db_result = state.get("db_query_result")
    med_info = state.get("medication_context")
    symptom_logs = state.get("symptom_logs", [])
    adherence_summary = state.get("adherence_summary")
    behavior_signal = state.get("behavior_signal")

    # ============================================================
    # BASE SAFETY + STYLE SYSTEM PROMPT
    # ============================================================

    SYSTEM_PROMPT = """
You are the final response generator for a safety-first medication adherence assistant.

Your rules:
- NEVER diagnose.
- NEVER recommend changing medication or dosage.
- NEVER give personalized medical advice.
- NEVER guess causes of symptoms.
- Keep tone calm, supportive, and non-judgmental.
- If discussing health risks, speak in general terms only.
- Encourage users to consult their healthcare provider for decisions.
- If user data was retrieved (DB results), present it factually without interpretation.
- Keep responses concise and clear.

Output ONLY the final chat response text.
"""

    # ============================================================
    # BUILD CONTEXT FOR LLM
    # ============================================================

    user_context = ""

    # 1. Education content
    if education:
        user_context += f"\n[EDUCATION_CONTENT]\n{education}\n"

    # 2. DB Query result
    if db_result:
        user_context += f"\n[DB_RESULT]\n{db_result}\n"

    # 3. Medication RAG Info
    if med_info:
        user_context += f"\n[MEDICATION_INFO]\n{med_info}\n"

    # 4. Symptom logs (session only)
    if symptom_logs:
        user_context += f"\n[SYMPTOM_LOGS]\n{symptom_logs}\n"

    # 5. Adherence conversation summary
    if adherence_summary:
        user_context += f"\n[ADHERENCE_BEHAVIOR]\n{adherence_summary}\n"

    # Behavior tag for motivational tone
    if behavior_signal:
        user_context += f"\n[BEHAVIOR_SIGNAL]\n{behavior_signal}\n"

    # ============================================================
    # ROUTING LOGIC (intents)
    # ============================================================

    # SIMPLE SMALLTALK
    if intent == "smalltalk":
        prompt = SYSTEM_PROMPT + f"""
The user is making smalltalk. Respond with a friendly, short message.

User message:
{state["user_input"]}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state
        

    # FALLBACK
    if intent == "fallback":
        
            state["response"]= "I'm not completely sure how to help with that, but I can assist with medication information, symptom logging, reminders, or your dose history."
            
        

    # EDUCATION RESPONSE
    if intent == "health_education":
        prompt = SYSTEM_PROMPT + f"""
Use the [EDUCATION_CONTENT] to generate a final friendly, safe explanation.

{user_context}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state

    # MEDICATION QUERY (RAG)
    if intent == "medication_query":
        prompt = SYSTEM_PROMPT + f"""
The user asked about medication information. Use [MEDICATION_INFO] safely.

{user_context}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state

    # SYMPTOM LOGGING
    if intent == "symptom_logging":
        prompt = SYSTEM_PROMPT + f"""
Acknowledge the symptom, confirm it has been logged, and give non-medical safety advice.

{user_context}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state

    # ADHERENCE CONVERSATION ("I missed my dose", etc.)
    if intent == "adherence_conversation":
        prompt = SYSTEM_PROMPT + f"""
The user described medication-taking behavior.
Use the behavior signal to give supportive, non-judgmental guidance.
Do NOT give medical consequences or advice.

{user_context}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state

    # DB QUERY (dose history, schedule, etc.)
    if intent == "db_query":
        prompt = SYSTEM_PROMPT + f"""
Present the database results in a simple, factual, friendly way.
Do NOT interpret medically. Do NOT judge. Do NOT give advice.

{user_context}
"""
        final_text = llm.invoke(prompt)
        state["response"]=final_text.content
        return state

    # Should not reach here
    state["response"]= "I'm here to help. Could you rephrase that?"
    return state


# from chatbot.state import State
# from chatbot.llm import llm


# def response_generation_node(state: State):
#     """
#     Final node that generates natural language response based on all collected data.
    
#     Takes structured data from previous nodes and creates a user-friendly response.
#     """
    
#     user_input = state.get("user_input", "")
#     intent = state.get("intent", "fallback")
    
#     # Collect all context from previous nodes
#     db_result = state.get("db_query_result")
#     medication_context = state.get("medication_context")
#     symptom_logs = state.get("symptom_logs")
#     education_content = state.get("education_content")
#     adherence_summary = state.get("adherence_summary")
    
#     # Build context for LLM
#     context_parts = []
    
#     # Add DB query results
#     if db_result and db_result.get("result"):
#         context_parts.append(f"Database Query Result: {db_result}")
    
#     # Add medication context
#     if medication_context and not medication_context.get("empty"):
#         context_parts.append(f"Medication Information: {medication_context}")
    
#     # Add symptom logs
#     if symptom_logs:
#         context_parts.append(f"Symptom Log: {symptom_logs}")
    
#     # Add education content
#     if education_content:
#         context_parts.append(f"Educational Content: {education_content}")
    
#     # Add adherence summary
#     if adherence_summary:
#         context_parts.append(f"Adherence Information: {adherence_summary}")
    
#     # Build prompt
#     if context_parts:
#         context_str = "\n\n".join(context_parts)
        
#         prompt = f"""You are a helpful medication adherence assistant. 

# Based on the following information, provide a clear, friendly, and helpful response to the user.

# User's Question: {user_input}

# Available Information:
# {context_str}

# Instructions:
# - Be conversational and empathetic
# - If providing medication information, be accurate but note you're not replacing medical advice
# - If showing schedule/dose information, format it clearly
# - If no relevant data was found, politely acknowledge this
# - Keep responses concise (2-4 sentences unless more detail is needed)

# Response:"""
#     else:
#         # No context available - generic response
#         prompt = f"""You are a helpful medication adherence assistant.

# User said: {user_input}

# Provide a brief, helpful response. If you cannot answer the question, politely explain what you can help with instead.

# Response:"""
    
#     # Generate response
#     try:
#         llm_response = llm.invoke(prompt)
        
#         # Extract text from AIMessage
#         if hasattr(llm_response, 'content'):
#             response_text = llm_response.content
#         elif isinstance(llm_response, str):
#             response_text = llm_response
#         else:
#             response_text = str(llm_response)
        
#         # Debug logging
#         print(f"\n🤖 Response Generated:")
#         print(f"   Context parts: {len(context_parts)}")
#         print(f"   Response: {response_text[:150]}...")
        
#     except Exception as e:
#         print(f"❌ Error generating response: {e}")
#         response_text = "I'm having trouble generating a response right now. Please try again."
    
#     # ✅ CRITICAL: Store response in state and return state
#     state["response"] = response_text
    
#     return state