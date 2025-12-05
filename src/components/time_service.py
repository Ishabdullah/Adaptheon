from datetime import datetime
from components.temporal_awareness import (
    get_current_date,
    detect_temporal_intent,
    should_use_external_sources,
    KNOWLEDGE_CUTOFF
)


def get_now():
    """
    Return current local time info from the device clock.
    """
    now = datetime.now()
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "date_obj": now.date(),
    }


def get_knowledge_cutoff_info():
    """Return information about the LLM's knowledge cutoff"""
    current = get_current_date()
    return {
        "cutoff_date": str(KNOWLEDGE_CUTOFF),
        "current_date": str(current),
        "days_since_cutoff": (current - KNOWLEDGE_CUTOFF).days,
        "is_current_after_cutoff": current > KNOWLEDGE_CUTOFF,
    }
