"""
Feedback Context Module for Adaptheon

Retrieves relevant feedback and builds context snippets to inject into LLM prompts.
"""

from typing import List, Optional, Dict, Any
from feedback_store import FeedbackStore, FeedbackExtraction, FeedbackEvent
from components.semantic_utils import text_to_vector, cosine_similarity


def get_relevant_feedback(
    conversation_id: str,
    current_query: str,
    feedback_store: FeedbackStore,
    max_results: int = 5,
    similarity_threshold: float = 0.2
) -> List[tuple[FeedbackEvent, FeedbackExtraction]]:
    """
    Get relevant feedback for current query.

    Args:
        conversation_id: Current conversation ID
        current_query: User's current question
        feedback_store: FeedbackStore instance
        max_results: Maximum number of feedback items to return
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        List of (FeedbackEvent, FeedbackExtraction) tuples, sorted by relevance
    """

    # Get all feedback for this conversation
    feedback_events = feedback_store.get_feedback_events(conversation_id)

    if not feedback_events:
        return []

    # Get extractions for each event
    feedback_pairs = []
    for event in feedback_events:
        extractions = feedback_store.get_extractions_for_event(event.id)
        for extraction in extractions:
            feedback_pairs.append((event, extraction))

    if not feedback_pairs:
        return []

    # Compute relevance scores
    query_vec = text_to_vector(current_query.lower())
    scored_feedback = []

    for event, extraction in feedback_pairs:
        # Compute similarity to event's raw text
        event_vec = text_to_vector(event.raw_text.lower())
        similarity = cosine_similarity(query_vec, event_vec)

        # Boost score for factual corrections
        if "CORRECTION_FACT" in event.feedback_types:
            similarity *= 1.3

        # Boost if corrected facts mention keywords from current query
        if extraction.corrected_facts:
            facts_text = str(extraction.corrected_facts).lower()
            if any(word in facts_text for word in current_query.lower().split()):
                similarity *= 1.2

        # Boost if preferred tools are relevant
        if extraction.preferred_tools:
            # Check if query mentions tools
            if any(tool in current_query.lower() for tool in extraction.preferred_tools):
                similarity *= 1.1

        # Filter by threshold
        if similarity >= similarity_threshold:
            scored_feedback.append((similarity, event, extraction))

    # Sort by relevance score (descending)
    scored_feedback.sort(key=lambda x: x[0], reverse=True)

    # Return top results
    return [(event, extraction) for _, event, extraction in scored_feedback[:max_results]]


def build_feedback_context_snippet(
    feedback_list: List[tuple[FeedbackEvent, FeedbackExtraction]],
    max_length: int = 500
) -> str:
    """
    Build a compact feedback context snippet for LLM injection.

    Args:
        feedback_list: List of (FeedbackEvent, FeedbackExtraction) tuples
        max_length: Maximum character length of snippet

    Returns:
        Formatted context string
    """

    if not feedback_list:
        return ""

    snippets = []

    for event, extraction in feedback_list:
        # Build snippet for this feedback item
        parts = []

        # Corrected facts
        if extraction.corrected_facts:
            facts_str = str(extraction.corrected_facts)
            if len(facts_str) > 100:
                facts_str = facts_str[:97] + "..."
            parts.append(f"User previously corrected: {facts_str}")

        # Preferred tools
        if extraction.preferred_tools:
            tools_str = ", ".join(extraction.preferred_tools)
            parts.append(f"User prefers tools: {tools_str}")

        # Style preferences
        if extraction.style_prefs:
            parts.append(f"Style preference: {extraction.style_prefs}")

        # Time sensitivity
        if extraction.time_sensitivity_notes:
            parts.append(f"Time-sensitive requirement: {extraction.time_sensitivity_notes}")

        # Severity indicator
        if event.severity == "major":
            parts.append("(IMPORTANT)")

        snippet = " | ".join(parts)
        snippets.append(f"- {snippet}")

    # Combine all snippets
    full_context = "\n".join(snippets)

    # Truncate if too long
    if len(full_context) > max_length:
        full_context = full_context[:max_length-3] + "..."

    # Wrap in feedback header
    if snippets:
        return f"[USER FEEDBACK/CORRECTIONS]:\n{full_context}\n"

    return ""


def get_feedback_summary(
    feedback_store: FeedbackStore,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a summary of feedback statistics.

    Args:
        feedback_store: FeedbackStore instance
        conversation_id: Optional conversation ID to filter by

    Returns:
        Dictionary with feedback statistics
    """

    if conversation_id:
        events = feedback_store.get_feedback_events(conversation_id)
        extractions = feedback_store.get_all_extractions(conversation_id)
    else:
        # Get all feedback
        all_events_data = feedback_store._load(feedback_store.files["feedback_events"])
        events = [FeedbackEvent(**e) for e in all_events_data]

        all_extractions_data = feedback_store._load(feedback_store.files["feedback_extractions"])
        extractions = [FeedbackExtraction(**e) for e in all_extractions_data]

    # Count by type
    type_counts = {}
    for event in events:
        for feedback_type in event.feedback_types:
            type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1

    # Count by severity
    severity_counts = {}
    for event in events:
        severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1

    # Count preferred tools
    tool_mentions = {}
    for extraction in extractions:
        for tool in extraction.preferred_tools:
            tool_mentions[tool] = tool_mentions.get(tool, 0) + 1

    # Count time-sensitive notes
    time_sensitive_count = sum(1 for e in extractions if e.time_sensitivity_notes)

    return {
        "total_feedback_events": len(events),
        "total_extractions": len(extractions),
        "feedback_by_type": type_counts,
        "feedback_by_severity": severity_counts,
        "tool_preferences": tool_mentions,
        "time_sensitive_feedback_count": time_sensitive_count,
    }


def get_domain_specific_feedback(
    feedback_store: FeedbackStore,
    domain: str,
    conversation_id: Optional[str] = None
) -> List[tuple[FeedbackEvent, FeedbackExtraction]]:
    """
    Get feedback related to a specific domain (e.g., "sports", "finance", "weather").

    Args:
        feedback_store: FeedbackStore instance
        domain: Domain to filter by
        conversation_id: Optional conversation ID

    Returns:
        List of relevant feedback
    """

    # Keywords for each domain
    DOMAIN_KEYWORDS = {
        "sports": ["game", "score", "team", "player", "match", "espn", "giants", "nfl", "nba"],
        "finance": ["price", "stock", "bitcoin", "crypto", "market", "trading", "dollar"],
        "weather": ["weather", "temperature", "forecast", "rain", "sunny", "climate"],
        "politics": ["president", "election", "government", "congress", "senate", "policy"],
        "science": ["research", "study", "paper", "arxiv", "journal", "scientist"],
        "technology": ["software", "hardware", "github", "code", "algorithm", "api"],
    }

    keywords = DOMAIN_KEYWORDS.get(domain.lower(), [])

    if not keywords:
        return []

    # Get all extractions
    if conversation_id:
        events = feedback_store.get_feedback_events(conversation_id)
    else:
        all_events_data = feedback_store._load(feedback_store.files["feedback_events"])
        events = [FeedbackEvent(**e) for e in all_events_data]

    # Filter by domain keywords
    relevant_feedback = []
    for event in events:
        event_text = event.raw_text.lower()

        # Check if any domain keyword appears in feedback
        if any(keyword in event_text for keyword in keywords):
            extractions = feedback_store.get_extractions_for_event(event.id)
            for extraction in extractions:
                relevant_feedback.append((event, extraction))

    return relevant_feedback


def format_feedback_for_logging(
    event: FeedbackEvent,
    extraction: FeedbackExtraction
) -> str:
    """
    Format feedback for structured logging.

    Args:
        event: FeedbackEvent
        extraction: FeedbackExtraction

    Returns:
        Formatted string for logging
    """

    parts = [
        f"FeedbackEvent[{event.id[:8]}]:",
        f"  Types: {', '.join(event.feedback_types)}",
        f"  Severity: {event.severity}",
        f"  Raw: {event.raw_text[:100]}{'...' if len(event.raw_text) > 100 else ''}",
    ]

    if extraction.corrected_facts:
        parts.append(f"  Corrected Facts: {extraction.corrected_facts}")

    if extraction.preferred_tools:
        parts.append(f"  Preferred Tools: {', '.join(extraction.preferred_tools)}")

    if extraction.style_prefs:
        parts.append(f"  Style: {extraction.style_prefs}")

    if extraction.time_sensitivity_notes:
        parts.append(f"  Time-Sensitive: {extraction.time_sensitivity_notes}")

    return "\n".join(parts)
