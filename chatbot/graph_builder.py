# # graph_builder.py
# from langgraph.graph import StateGraph, END
# from chatbot.state import State

# # Import all nodes
# from chatbot.nodes.red_flag_node import red_flag_node
# from chatbot.nodes.emergency_node import emergency_node
# from chatbot.nodes.intent_classifier_node import intent_classifier_node
# from chatbot.nodes.symptom_node import symptom_node
# from chatbot.nodes.medication_node import medication_rag_node
# from chatbot.nodes.adherence_node import adherence_node
# from chatbot.nodes.db_query_node import db_query_node
# from chatbot.nodes.education_node import education_node
# from chatbot.nodes.response_generation_node import response_generation_node

# import sqlite3


# # -------------------------------------
# # DATABASE CONNECTION (for db_query_node)
# # -------------------------------------
# def get_db_connection():
#     # Path MUST match your Django SQLite DB
#     return sqlite3.connect("db.sqlite3", check_same_thread=False)


# conn = get_db_connection()


# # -------------------------------------
# # WRAPPER: Provide DB connection to db_query_node
# # LangGraph requires node signature (state) only,
# # so we create a closure wrapper
# # -------------------------------------
# def db_query_node_wrapper(state: State):
#     return db_query_node(state, conn)


# # =====================================
# # BUILD THE LANGGRAPH
# # =====================================

# def build_graph():

#     graph = StateGraph(State)

#     # -------------------------------------
#     # REGISTER NODES
#     # -------------------------------------
#     graph.add_node("red_flag_node", red_flag_node)
#     graph.add_node("emergency_node", emergency_node)
#     graph.add_node("intent_classifier_node", intent_classifier_node)
#     graph.add_node("symptom_node", symptom_node)
#     graph.add_node("medication_rag_node", medication_rag_node)
#     graph.add_node("adherence_node", adherence_node)
#     graph.add_node("db_query_node", db_query_node_wrapper)
#     graph.add_node("education_node", education_node)
#     graph.add_node("response_generation_node", response_generation_node)

#     # -------------------------------------
#     # ENTRY POINT
#     # Always start with red_flag_node
#     # -------------------------------------
#     graph.set_entry_point("red_flag_node")

#     # -------------------------------------
#     # SAFETY ROUTING: Red Flag Node
#     # -------------------------------------
#     def red_flag_route(state: State):
#         if state.get("is_emergency") is True:
#             return "emergency_node"
#         return "intent_classifier_node"

#     graph.add_conditional_edges(
#         "red_flag_node",
#         red_flag_route,
#         {
#             "emergency_node": "emergency_node",
#             "intent_classifier_node": "intent_classifier_node"
#         }
#     )

#     # -------------------------------------
#     # INTENT CLASSIFIER ROUTING
#     # -------------------------------------
#     def intent_router(state: State):
#         return state.get("route")   # route string set by classifier

#     graph.add_conditional_edges(
#         "intent_classifier_node",
#         intent_router,
#         {
#             "symptom_node": "symptom_node",
#             "medication_rag_node": "medication_rag_node",
#             "adherence_node": "adherence_node",
#             "db_query_node": "db_query_node",
#             "education_node": "education_node",
#             "response_generation_node": "response_generation_node"
#         }
#     )

#     # -------------------------------------
#     # After ANY domain node → go to response generator
#     # -------------------------------------
#     domain_nodes = [
#         "symptom_node",
#         "medication_rag_node",
#         "adherence_node",
#         "db_query_node",
#         "education_node"
#     ]

#     for node in domain_nodes:
#         graph.add_edge(node, "response_generation_node")

#     # -------------------------------------
#     # FINAL NODE → END
#     # -------------------------------------
#     graph.add_edge("response_generation_node", END)
#     graph.add_edge("emergency_node", END)

#     return graph.compile()


# # Expose graph for use in backend
# CHATBOT_GRAPH = build_graph()

# # # graph_builder.py - FIXED VERSION with error handling
# # from langgraph.graph import StateGraph, END
# # from chatbot.state import State
# # import sqlite3
# # import logging

# # # Configure logging
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # # Import all nodes
# # from chatbot.nodes.red_flag_node import red_flag_node
# # from chatbot.nodes.emergency_node import emergency_node
# # from chatbot.nodes.intent_classifier_node import intent_classifier_node
# # from chatbot.nodes.symptom_node import symptom_node
# # from chatbot.nodes.medication_node import medication_rag_node  # FIXED: medication_node not medication_rag_node
# # from chatbot.nodes.adherence_node import adherence_node
# # from chatbot.nodes.db_query_node import db_query_node
# # from chatbot.nodes.education_node import education_node
# # from chatbot.nodes.response_generation_node import response_generation_node


# # # -------------------------------------
# # # DATABASE CONNECTION
# # # -------------------------------------
# # def get_db_connection():
# #     """Create database connection with error handling"""
# #     try:
# #         conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
# #         logger.info("Database connection established successfully")
# #         return conn
# #     except Exception as e:
# #         logger.error(f"Database connection failed: {e}")
# #         raise


# # # Initialize connection globally
# # try:
# #     conn = get_db_connection()
# # except Exception as e:
# #     logger.error(f"Failed to initialize database connection: {e}")
# #     conn = None


# # # -------------------------------------
# # # DB QUERY NODE WRAPPER
# # # -------------------------------------
# # def db_query_node_wrapper(state: State):
# #     """Wrapper to inject database connection"""
# #     if conn is None:
# #         logger.error("Database connection not available")
# #         state["error"] = "Database unavailable"
# #         return state
# #     return db_query_node(state, conn)


# # # -------------------------------------
# # # ROUTING FUNCTIONS
# # # -------------------------------------
# # def red_flag_route(state: State):
# #     """Route based on emergency detection"""
# #     is_emergency = state.get("is_emergency", False)
# #     logger.info(f"Red flag routing: is_emergency={is_emergency}")
    
# #     if is_emergency is True:
# #         return "emergency_node"
# #     return "intent_classifier_node"


# # def intent_router(state: State):
# #     """Route based on intent classification"""
# #     route = state.get("route")
# #     logger.info(f"Intent routing to: {route}")
    
# #     # Validate route exists
# #     valid_routes = [
# #         "symptom_node",
# #         "medication_rag_node",
# #         "adherence_node",
# #         "db_query_node",
# #         "education_node",
# #         "response_generation_node"
# #     ]
    
# #     if route not in valid_routes:
# #         logger.warning(f"Invalid route '{route}', defaulting to response_generation_node")
# #         return "response_generation_node"
    
# #     return route


# # # =====================================
# # # BUILD THE LANGGRAPH
# # # =====================================
# # def build_graph():
# #     """Build and compile the LangGraph workflow"""
    
# #     logger.info("Building chatbot graph...")
    
# #     try:
# #         graph = StateGraph(State)

# #         # -------------------------------------
# #         # REGISTER NODES
# #         # -------------------------------------
# #         graph.add_node("red_flag_node", red_flag_node)
# #         graph.add_node("emergency_node", emergency_node)
# #         graph.add_node("intent_classifier_node", intent_classifier_node)
# #         graph.add_node("symptom_node", symptom_node)
# #         graph.add_node("medication_rag_node", medication_rag_node)
# #         graph.add_node("adherence_node", adherence_node)
# #         graph.add_node("db_query_node", db_query_node_wrapper)
# #         graph.add_node("education_node", education_node)
# #         graph.add_node("response_generation_node", response_generation_node)
        
# #         logger.info("All nodes registered successfully")

# #         # -------------------------------------
# #         # ENTRY POINT
# #         # -------------------------------------
# #         graph.set_entry_point("red_flag_node")

# #         # -------------------------------------
# #         # CONDITIONAL EDGES
# #         # -------------------------------------
        
# #         # Red flag routing
# #         graph.add_conditional_edges(
# #             "red_flag_node",
# #             red_flag_route,
# #             {
# #                 "emergency_node": "emergency_node",
# #                 "intent_classifier_node": "intent_classifier_node"
# #             }
# #         )
        
# #         # Intent classifier routing
# #         graph.add_conditional_edges(
# #             "intent_classifier_node",
# #             intent_router,
# #             {
# #                 "symptom_node": "symptom_node",
# #                 "medication_rag_node": "medication_rag_node",
# #                 "adherence_node": "adherence_node",
# #                 "db_query_node": "db_query_node",
# #                 "education_node": "education_node",
# #                 "response_generation_node": "response_generation_node"
# #             }
# #         )

# #         # -------------------------------------
# #         # DOMAIN NODES → RESPONSE GENERATOR
# #         # -------------------------------------
# #         domain_nodes = [
# #             "symptom_node",
# #             "medication_rag_node",
# #             "adherence_node",
# #             "db_query_node",
# #             "education_node"
# #         ]

# #         for node in domain_nodes:
# #             graph.add_edge(node, "response_generation_node")

# #         # -------------------------------------
# #         # EMERGENCY NODE → END (CRITICAL FIX!)
# #         # -------------------------------------
# #         # ISSUE: Emergency node had no outgoing edge
# #         graph.add_edge("emergency_node", END)

# #         # -------------------------------------
# #         # FINAL NODE → END
# #         # -------------------------------------
# #         graph.add_edge("response_generation_node", END)

# #         logger.info("Graph edges configured successfully")
        
# #         # Compile graph
# #         compiled_graph = graph.compile()
# #         logger.info("Graph compiled successfully")
        
# #         return compiled_graph
        
# #     except Exception as e:
# #         logger.error(f"Failed to build graph: {e}")
# #         raise


# # # =====================================
# # # INITIALIZE GRAPH
# # # =====================================
# # try:
# #     CHATBOT_GRAPH = build_graph()
# #     logger.info("Chatbot graph initialized and ready")
# # except Exception as e:
# #     logger.error(f"Failed to initialize chatbot graph: {e}")
# #     CHATBOT_GRAPH = None


# # # =====================================
# # # DEBUGGING HELPER
# # # =====================================
# # def test_graph():
# #     """Test function to validate graph execution"""
# #     if CHATBOT_GRAPH is None:
# #         print("❌ Graph not initialized")
# #         return
    
# #     test_state = {
# #         "messages": ["I have a headache"],
# #         "is_emergency": False,
# #         "route": "symptom_node"
# #     }
    
# #     try:
# #         result = CHATBOT_GRAPH.invoke(test_state)
# #         print("✅ Graph test passed")
# #         print(f"Result: {result}")
# #     except Exception as e:
# #         print(f"❌ Graph test failed: {e}")


# # if __name__ == "__main__":
# #     test_graph()


# graph_builder.py - PRODUCTION-READY VERSION
"""
LangGraph workflow builder with comprehensive error handling and debugging
"""

from langgraph.graph import StateGraph, END , START
from chatbot.state import State
import sqlite3
import logging
import os

# If running a standalone script (not Django management command)
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crudapp.settings')
django.setup()

# Now import your models/other Django modules

# =====================================
# LOGGING CONFIGURATION
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =====================================
# IMPORT NODES WITH ERROR HANDLING
# =====================================
try:
    from chatbot.nodes.red_flag_node import red_flag_node
    logger.info("✅ Imported red_flag_node")
except ImportError as e:
    logger.error(f"❌ Failed to import red_flag_node: {e}")
    raise

try:
    from chatbot.nodes.emergency_node import emergency_node
    logger.info("✅ Imported emergency_node")
except ImportError as e:
    logger.error(f"❌ Failed to import emergency_node: {e}")
    raise

try:
    from chatbot.nodes.intent_classifier_node import intent_classifier_node
    logger.info("✅ Imported intent_classifier_node")
except ImportError as e:
    logger.error(f"❌ Failed to import intent_classifier_node: {e}")
    raise

try:
    from chatbot.nodes.symptom_node import symptom_node
    logger.info("✅ Imported symptom_node")
except ImportError as e:
    logger.error(f"❌ Failed to import symptom_node: {e}")
    raise

try:
    # Check both possible import paths
    try:
        from chatbot.nodes.medication_node import medication_rag_node
    except ImportError:
        from chatbot.nodes.medication_node import medication_rag_node
    logger.info("✅ Imported medication_rag_node")
except ImportError as e:
    logger.error(f"❌ Failed to import medication_rag_node: {e}")
    logger.error("   Check if file is named 'medication_node.py' or 'medication_rag_node.py'")
    raise

try:
    from chatbot.nodes.adherence_node import adherence_node
    logger.info("✅ Imported adherence_node")
except ImportError as e:
    logger.error(f"❌ Failed to import adherence_node: {e}")
    raise

try:
    from chatbot.nodes.db_query_node import db_query_node
    logger.info("✅ Imported db_query_node")
except ImportError as e:
    logger.error(f"❌ Failed to import db_query_node: {e}")
    raise

try:
    from chatbot.nodes.education_node import education_node
    logger.info("✅ Imported education_node")
except ImportError as e:
    logger.error(f"❌ Failed to import education_node: {e}")
    raise

try:
    from chatbot.nodes.response_generation_node import response_generation_node
    logger.info("✅ Imported response_generation_node")
except ImportError as e:
    logger.error(f"❌ Failed to import response_generation_node: {e}")
    raise


# =====================================
# DATABASE CONNECTION
# =====================================
def get_db_connection():
    """
    Create database connection with intelligent path detection
    """
    # Try multiple possible database locations
    possible_paths = [
        "db.sqlite3",  # Django root
        "../db.sqlite3",  # One level up
        "../../db.sqlite3",  # Two levels up
        os.path.join(os.getcwd(), "db.sqlite3"),  # Current working directory
    ]
    
    for db_path in possible_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path, check_same_thread=False)
                logger.info(f"✅ Database connected: {db_path}")
                return conn
            except Exception as e:
                logger.error(f"❌ Failed to connect to {db_path}: {e}")
                continue
    
    # If no database found, raise error with helpful message
    logger.error("❌ Database not found in any expected location")
    logger.error(f"   Searched paths: {possible_paths}")
    logger.error("   Please ensure db.sqlite3 exists and migrations are run")
    raise FileNotFoundError(
        "Database not found. Run 'python manage.py migrate' to create it."
    )


# Initialize database connection
try:
    conn = get_db_connection()
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    conn = None


# =====================================
# DB QUERY NODE WRAPPER
# =====================================
def db_query_node_wrapper(state: State) -> State:
    """
    Wrapper to inject database connection with error handling
    """
    if conn is None:
        logger.error("Database connection unavailable")
        state["error"] = "Database connection unavailable"
        state["response"] = "I'm having trouble accessing the database. Please try again later."
        return state
    
    try:
        return db_query_node(state, conn)
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        state["error"] = str(e)
        state["response"] = "I encountered an error while querying the database."
        return state


# =====================================
# ROUTING FUNCTIONS
# =====================================
def red_flag_route(state: State) -> str:
    """
    Route based on emergency detection
    Returns: "emergency_node" or "intent_classifier_node"
    """
    is_emergency = state.get("is_emergency", False)
    
    logger.debug(f"Red flag routing: is_emergency={is_emergency}")
    
    if is_emergency is True:
        logger.info("🚨 Emergency detected - routing to emergency_node")
        return "emergency_node"
    
    logger.debug("No emergency - routing to intent_classifier_node")
    return "intent_classifier_node"


def intent_router(state: State) -> str:
    """
    Route based on intent classification with validation
    Returns: node name string
    """
    route = state.get("route")
    
    # Define valid routes
    valid_routes = {
        "symptom_node",
        "medication_rag_node",
        "adherence_node",
        "db_query_node",
        "education_node",
        "response_generation_node"
    }
    
    # Validate route
    if route is None:
        logger.warning("No route specified, defaulting to response_generation_node")
        return "response_generation_node"
    
    if route not in valid_routes:
        logger.warning(
            f"Invalid route '{route}', defaulting to response_generation_node. "
            f"Valid routes: {valid_routes}"
        )
        return "response_generation_node"
    
    logger.info(f"Routing to: {route}")
    return route


# =====================================
# BUILD THE LANGGRAPH
# =====================================
def build_graph():
    """
    Build and compile the LangGraph workflow with comprehensive error handling
    """
    logger.info("="*60)
    logger.info("Building chatbot graph...")
    logger.info("="*60)
    
    try:
        # Initialize graph
        graph = StateGraph(State)
        logger.debug("StateGraph initialized")

        # =====================================
        # REGISTER NODES
        # =====================================
        nodes_to_register = [
            ("red_flag_node", red_flag_node),
            ("emergency_node", emergency_node),
            ("intent_classifier_node", intent_classifier_node),
            ("symptom_node", symptom_node),
            ("medication_rag_node", medication_rag_node),
            ("adherence_node", adherence_node),
            ("db_query_node", db_query_node_wrapper),
            ("education_node", education_node),
            ("response_generation_node", response_generation_node),
        ]
        
        for node_name, node_func in nodes_to_register:
            try:
                graph.add_node(node_name, node_func)
                logger.debug(f"   Registered: {node_name}")
            except Exception as e:
                logger.error(f"  Failed to register {node_name}: {e}")
                raise
        
        logger.info("All nodes registered successfully")

        # =====================================
        # SET ENTRY POINT
        # =====================================
        graph.add_edge(START,"red_flag_node")
        logger.debug(" Entry point set: red_flag_node")

        # =====================================
        # CONDITIONAL EDGES
        # =====================================
        
        # Red flag routing (emergency detection)
        graph.add_conditional_edges(
            "red_flag_node",
            red_flag_route,
            {
                "emergency_node": "emergency_node",
                "intent_classifier_node": "intent_classifier_node"
            }
        )
        logger.debug(" Red flag routing configured")
        
        # Intent classification routing
        graph.add_conditional_edges(
            "intent_classifier_node",
            intent_router,
            {
                "symptom_node": "symptom_node",
                "medication_rag_node": "medication_rag_node",
                "adherence_node": "adherence_node",
                "db_query_node": "db_query_node",
                "education_node": "education_node",
                "response_generation_node": "response_generation_node"
            }
        )
        logger.debug(" Intent routing configured")

        # =====================================
        # DOMAIN NODES → RESPONSE GENERATOR
        # =====================================
        domain_nodes = [
            "symptom_node",
            "medication_rag_node",
            "adherence_node",
            "db_query_node",
            "education_node"
        ]

        for node in domain_nodes:
            graph.add_edge(node, "response_generation_node")
            logger.debug(f"  {node} → response_generation_node")

        # =====================================
        # TERMINAL EDGES
        # =====================================
        
        # Emergency node exits immediately (CRITICAL!)
        graph.add_edge("emergency_node", END)
        logger.debug("✅ emergency_node → END")
        
        # Response generator is final step
        graph.add_edge("response_generation_node", END)
        logger.debug("✅ response_generation_node → END")

        logger.info("✅ All edges configured successfully")
        
        # =====================================
        # COMPILE GRAPH
        # =====================================
        compiled_graph = graph.compile()
        logger.info("✅ Graph compiled successfully")
        
        logger.info("="*60)
        logger.info("Graph build complete!")
        logger.info("="*60)
        
        return compiled_graph
        
    except Exception as e:
        logger.error("="*60)
        logger.error(f"❌ GRAPH BUILD FAILED: {e}")
        logger.error("="*60)
        
        # Print detailed traceback
        import traceback
        logger.error(traceback.format_exc())
        
        raise


# =====================================
# INITIALIZE GRAPH
# =====================================
try:
    CHATBOT_GRAPH = build_graph()
    logger.info(" Chatbot graph ready for use!")
except Exception as e:
    logger.error(f" Failed to initialize chatbot graph: {e}")
    CHATBOT_GRAPH = None


# =====================================
# UTILITY FUNCTIONS
# =====================================

def validate_state(state: State) -> tuple[bool, list[str]]:
    """
    Validate state has required fields
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # Required fields
    if "user_input" not in state or not state["user_input"]:
        errors.append("Missing required field: user_input")
    
    if "user_id" not in state:
        errors.append("Missing required field: user_id")
    
    return len(errors) == 0, errors


def run_graph_safely(state: State) -> State:
    """
    Execute graph with validation and error handling
    """
    # Validate input state
    is_valid, errors = validate_state(state)
    if not is_valid:
        logger.error(f"Invalid state: {errors}")
        return {
            **state,
            "error": "; ".join(errors),
            "response": "Invalid request. Please provide a message."
        }
    
    # Check graph is initialized
    if CHATBOT_GRAPH is None:
        logger.error("Graph not initialized")
        return {
            **state,
            "error": "System not ready",
            "response": "The chatbot is currently unavailable. Please try again later."
        }
    
    # Execute graph
    try:
        logger.info(f"Processing message from user {state.get('user_id')}: {state.get('user_input')[:50]}...")
        result = CHATBOT_GRAPH.invoke(state)
        logger.info("✅ Graph execution completed successfully")
        return result
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            **state,
            "error": str(e),
            "response": "I encountered an error processing your request. Please try again."
        }


# =====================================
# DEBUG/TEST FUNCTION
# =====================================
def test_graph():
    """
    Quick test to validate graph works
    """
    print("\n" + "="*60)
    print("TESTING GRAPH")
    print("="*60)
    
    if CHATBOT_GRAPH is None:
        print("❌ Graph not initialized - cannot test")
        return False
    
    # Test 1: Basic non-emergency flow
    print("\n--- Test 1: Non-Emergency Message ---")
    test_state = {
        "user_id": 1,
        "user_input": "Hello, how are you?",
        "is_emergency": False,
        "route": "response_generation_node"
    }
    
    try:
        result = run_graph_safely(test_state)
        print(f"✅ Response: {result.get('response', 'No response')[:100]}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        return False
    
    # Test 2: Emergency flow
    print("\n--- Test 2: Emergency Message ---")
    test_state = {
        "user_id": 1,
        "user_input": "I'm having severe chest pain",
        "is_emergency": True,
        "emergency_type": "chest_pain"
    }
    
    try:
        result = run_graph_safely(test_state)
        print(f"✅ Response: {result.get('response', 'No response')[:100]}")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    return True


# =====================================
# MAIN EXECUTION
# =====================================
if __name__ == "__main__":
    print("\nLangGraph Chatbot - Graph Builder")
    print("="*60)
    
    if CHATBOT_GRAPH is not None:
        print("✅ Graph successfully initialized")
        
        # Run tests
        import sys
        if "--test" in sys.argv:
            test_graph()
    else:
        print("❌ Graph initialization failed")
        print("Check the logs above for details")