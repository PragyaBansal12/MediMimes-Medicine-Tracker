from chatbot.state import State
from chatbot.llm import llm
from datetime import datetime, timedelta
import json
import re
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# If running a standalone script (not Django management command)
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crudapp.settings')
django.setup()

# Now import your models/other Django modules
SYMPTOM_EXTRACTION_PROMPT = """
Extract structured symptom data from the user's message.

Return ONLY a JSON object with this exact format:

{
  "symptom": <string>,
  "severity": <string or null>
}

Rules:
- Do NOT diagnose.
- Do NOT infer unmentioned symptoms.
- Only extract what is explicitly stated.
- Severity can be: mild, moderate, severe, or null.
- Do NOT extract duration (we don't store it).
- If you are unsure, put null.

Examples:

Input: "I have a headache"
Output: {"symptom": "headache", "severity": null}

Input: "I've had severe nausea"
Output: {"symptom": "nausea", "severity": "severe"}

Input: "My stomach hurts a bit"
Output: {"symptom": "stomach pain", "severity": "mild"}
"""


def extract_symptom_from_text(text: str) -> Dict[str, Optional[str]]:
    """
    Extract symptom information from text using LLM.
    Matches your simplified model (no duration field).
    """
    if not text.strip():
        return {"symptom": None, "severity": None}
    
    prompt = SYMPTOM_EXTRACTION_PROMPT + f"\n\nUser message: {text}\n\nReturn ONLY the JSON object."
    
    try:
        raw = llm.invoke(prompt)
        
        # Extract content from AIMessage
        if hasattr(raw, 'content'):
            text_response = raw.content
        else:
            text_response = str(raw)
        
        # Parse JSON
        try:
            parsed = json.loads(text_response)
        except json.JSONDecodeError:
            # Try to extract JSON with regex
            match = re.search(r'\{[\s\S]*?\}', text_response)
            if match:
                parsed = json.loads(match.group())
            else:
                logger.warning("Could not parse LLM response as JSON")
                parsed = {"symptom": None, "severity": None}
        
        # Clean and validate
        symptom = parsed.get("symptom")
        if symptom:
            symptom = symptom.strip()[:500]  # Limit to model field length
        
        severity = parsed.get("severity")
        if severity:
            severity = severity.lower()
            if severity not in ['mild', 'moderate', 'severe']:
                severity = None
        
        return {
            "symptom": symptom,
            "severity": severity
        }
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return {"symptom": None, "severity": None}


def save_symptom_to_db(user_id: int, symptom: str, severity: Optional[str]) -> Optional[int]:
    """
    Args:
        user_id: User ID
        symptom: Symptom description
        severity: mild/moderate/severe or None
        
    Returns:
        Symptom ID if saved, None if failed
    """
    try:
        # Import here to avoid circular imports
        from django.contrib.auth.models import User
        from medicines.models import Symptom
        
        # Get user instance
        user = User.objects.get(id=user_id)
        
        # Create symptom record (no duration field)
        symptom_obj = Symptom.objects.create(
            user=user,
            symptom=symptom,
            severity=severity
        )
        
        logger.info(f"Saved symptom to DB via ORM: user={user_id}, symptom={symptom}, id={symptom_obj.id}")
        return symptom_obj.id
        
    except User.DoesNotExist:
        logger.error(f"User with id={user_id} does not exist")
        return None
    except Exception as e:
        logger.error(f"Failed to save symptom via ORM: {e}")
        return None


def cleanup_old_symptoms(user_id: int):
    """
    Clean up old symptom logs for a user.
    Keeps only last 50 entries and last 7 days.
    
    Using Django ORM.
    """
    try:
        from medicines.models import Symptom
        from django.utils import timezone

        seven_days_ago = timezone.now() - timedelta(days=7)
        

        deleted_old = Symptom.objects.filter(
            user_id=user_id,
            timestamp__lt=seven_days_ago
        ).delete()[0]

        recent_ids = Symptom.objects.filter(
            user_id=user_id
        ).order_by('-timestamp').values_list('id', flat=True)[:50]
        
        # Delete symptoms not in recent_ids
        deleted_excess = Symptom.objects.filter(
            user_id=user_id
        ).exclude(id__in=recent_ids).delete()[0]
        
        if deleted_old > 0 or deleted_excess > 0:
            logger.info(f"Cleaned up symptoms for user {user_id}: {deleted_old} old, {deleted_excess} excess")
            
    except Exception as e:
        logger.error(f"Failed to cleanup old symptoms: {e}")


def symptom_node(state: State) -> State:
    """
    Extract symptoms from user input and log using Django ORM.
    Matches your simplified Symptom model (no duration field).
    
    State updates:
    - symptom_logs: Append new symptom entry
    - Each entry has: symptom, severity, timestamp, (db_id if logged)
    
    Returns updated State dict.
    """
    # Import Django ORM models
    try:
        from django.contrib.auth.models import User
        from medicines.models import Symptom
    except ImportError:
        logger.error("Django models not available. Make sure Django is properly set up.")
        return state
    
    user_text = state.get("user_input", "")
    user_id = state.get("user_id")
    
    if not user_text:
        logger.debug("Empty user input, skipping symptom extraction")
        return state
    
    # 1. Extract symptom using LLM (no duration field)
    extracted = extract_symptom_from_text(user_text)
    symptom = extracted["symptom"]
    severity = extracted["severity"]
    
    # 2. Build structured entry for session state (no duration)
    entry: Dict[str, Any] = {
        "symptom": symptom,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # 3. Save to database (if user_id exists and symptom extracted)
    db_id = None
    if user_id and symptom:
        try:
            # Check if user exists
            user_exists = User.objects.filter(id=user_id).exists()
            if user_exists:
                db_id = save_symptom_to_db(
                    user_id=user_id,
                    symptom=symptom,
                    severity=severity
                )
                
                # Cleanup old entries
                if db_id:
                    cleanup_old_symptoms(user_id)
            else:
                logger.warning(f"User with id={user_id} does not exist, skipping DB save")
        except Exception as e:
            logger.error(f"Failed to save symptom: {e}")
    
    # Add DB ID to entry if saved
    if db_id:
        entry["db_id"] = db_id
    
    # 4. Append to symptom logs (session state)
    logs = state.get("symptom_logs", [])
    logs.append(entry)
    state["symptom_logs"] = logs
    
    # 5. DO NOT generate response text here
    # response_generation_node will handle user messaging
    
    return state


# ============================================================
# HELPER FUNCTIONS FOR BACKEND/DASHBOARD
# ============================================================

def get_user_symptoms(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get symptom history for a user using Django ORM.
    """
    try:
        from medicines.models import Symptom
        
        symptoms = Symptom.objects.filter(
            user_id=user_id
        ).order_by('-timestamp')[:limit]
        
        return [symptom.to_dict() for symptom in symptoms]
        
    except Exception as e:
        logger.error(f"Failed to get user symptoms: {e}")
        return []


def get_symptom_trends(user_id: int, days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Get symptom trends for dashboard visualization using Django ORM.
    Matches your simplified model (no duration field).
    """
    try:
        from medicines.models import Symptom
        from django.utils import timezone
        from django.db.models import Count
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get symptoms in timeframe
        symptoms = Symptom.objects.filter(
            user_id=user_id,
            timestamp__gte=cutoff_date
        )
        
        # Get symptom frequency
        symptom_frequency = (
            symptoms.values('symptom')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Get severity distribution
        severity_distribution = (
            symptoms.exclude(severity__isnull=True)
            .values('severity')
            .annotate(count=Count('id'))
            .order_by('severity')
        )
        
        # Convert to dict
        severity_dict = {
            item['severity']: item['count']
            for item in severity_distribution
        }
        
        # Convert symptom frequency to list of dicts
        symptom_freq_list = [
            {"symptom": item['symptom'], "count": item['count']}
            for item in symptom_frequency
        ]
        
        return {
            "days_analyzed": days,
            "total_symptoms": symptoms.count(),
            "symptom_frequency": symptom_freq_list,
            "severity_distribution": severity_dict
        }
        
    except Exception as e:
        logger.error(f"Failed to get symptom trends: {e}")
        return None