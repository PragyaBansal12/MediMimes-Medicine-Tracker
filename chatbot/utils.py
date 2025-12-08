# chatbot/utils.py
import os
import django
import sys
from django.apps import apps

def setup_django_for_chatbot():
    """Setup Django environment for chatbot"""
    # Find the project root 
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Setup Django
    if not apps.ready:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crudapp.settings")
        django.setup()





# chatbot/utils.py
import threading
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class ChatbotWrapper:
    """Simple wrapper for your chatbot graph"""
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.graph = None
    
    def initialize(self):
        """Lazy initialization of the chatbot graph"""
        if self.graph is None:
            with self._lock:
                if self.graph is None:
                    try:
                        from .graph_builder import build_graph
                        self.graph = build_graph()
                        logger.info("Chatbot graph initialized")
                    except Exception as e:
                        logger.error(f"Failed to initialize chatbot: {e}")
                        raise
    
    def process(self, user_input, user_id=None, context=None):
        """
        Process user message.
        
        Args:
            user_input: str - user message
            user_id: str/int - user identifier
            context: dict - conversation context
            
        Returns:
            dict - chatbot response
        """
        self.initialize()
        
        # Prepare state
        state = {
            "user_id": user_id,
            "user_input": user_input,
            "context": context or {},
            "timestamp": timezone.now(),
            "intent": None,
            "is_emergency": False,
            "response": "",
            "symptom_logs": [],
            "conversation_history": context.get('history', []) if context else []
        }
        
        # Generate thread ID
        thread_id = f"user_{user_id}" if user_id else f"anon_{hash(user_input)}"
        
        try:
            result = self.graph.invoke(
                state,
                config={"configurable": {"thread_id": thread_id}}
            )
            
            return {
                "success": True,
                "response": result.get("response", "I'm sorry, I couldn't process that."),
                "intent": result.get("intent", "fallback"),
                "is_emergency": result.get("is_emergency", False),
                "symptoms": result.get("symptom_logs", []),
                "suggestions": result.get("suggestions", []),
                "query_type": result.get("query_type"),
                "metadata": {
                    "timestamp": result.get("timestamp"),
                    "route": result.get("route")
                }
            }
            
        except Exception as e:
            logger.error(f"Chatbot processing error: {e}")
            return {
                "success": False,
                "response": "I'm experiencing technical difficulties. Please try again.",
                "error": str(e)
            }

# Singleton instance
chatbot = ChatbotWrapper()