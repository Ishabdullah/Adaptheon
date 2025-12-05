"""
Tool Learning Module for Adaptheon

Analyzes feedback patterns and tool use events to learn routing rules.
Provides recommendations for when to use specific tools or domain fetchers.
"""

from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from feedback_store import FeedbackStore, FeedbackType, ToolUseEvent


class ToolLearningEngine:
    """
    Learns from feedback and tool use patterns to recommend routing rules.
    """

    def __init__(self, feedback_store: FeedbackStore):
        self.feedback_store = feedback_store

    def analyze_tool_performance(self) -> Dict[str, Dict[str, any]]:
        """
        Analyze tool use events to compute success rates and patterns.

        Returns:
            Dict mapping tool_name -> {
                "total_uses": int,
                "successful_uses": int,
                "success_rate": float,
                "common_inputs": List[str],
                "avg_response_useful": bool
            }
        """

        tool_use_events = self.feedback_store.get_tool_use_events()

        tool_stats = defaultdict(lambda: {
            "total_uses": 0,
            "successful_uses": 0,
            "success_rate": 0.0,
            "input_patterns": Counter(),
        })

        for event in tool_use_events:
            stats = tool_stats[event.tool_name]
            stats["total_uses"] += 1

            if event.success:
                stats["successful_uses"] += 1

            # Track input patterns (simplified)
            for key in event.inputs.keys():
                stats["input_patterns"][key] += 1

        # Compute success rates
        for tool_name, stats in tool_stats.items():
            if stats["total_uses"] > 0:
                stats["success_rate"] = stats["successful_uses"] / stats["total_uses"]

            # Convert Counter to list of common inputs
            stats["common_input_keys"] = [k for k, _ in stats["input_patterns"].most_common(5)]
            del stats["input_patterns"]

        return dict(tool_stats)

    def analyze_correction_patterns(self) -> Dict[str, List[str]]:
        """
        Analyze CORRECTION_TOOL_USE and CORRECTION_FACT feedback to identify patterns.

        Returns:
            Dict mapping domain/topic -> [recommended_tools]
        """

        # Get all feedback extractions
        all_extractions = self.feedback_store.get_all_extractions()

        # Get all feedback events to check types
        all_events_data = self.feedback_store._load(self.feedback_store.files["feedback_events"])

        # Build map: event_id -> event
        event_map = {e["id"]: e for e in all_events_data}

        # Track which tools users want for which topics
        topic_tool_recommendations = defaultdict(Counter)

        for extraction in all_extractions:
            event = event_map.get(extraction.feedback_event_id)
            if not event:
                continue

            # Only process correction feedback
            if not any("CORRECTION" in ft for ft in event["feedback_types"]):
                continue

            # Extract topic from corrected facts or raw text
            topic = "general"
            if extraction.corrected_facts and isinstance(extraction.corrected_facts, dict):
                topic = extraction.corrected_facts.get("topic", "general")

            # If no topic in facts, try to infer from raw text keywords
            if topic == "general":
                raw_text = event["raw_text"].lower()
                if any(word in raw_text for word in ["game", "score", "team", "sports"]):
                    topic = "sports"
                elif any(word in raw_text for word in ["price", "stock", "bitcoin", "crypto"]):
                    topic = "finance"
                elif any(word in raw_text for word in ["weather", "temperature", "forecast"]):
                    topic = "weather"
                elif any(word in raw_text for word in ["president", "election", "government"]):
                    topic = "politics"

            # Track recommended tools
            for tool in extraction.preferred_tools:
                topic_tool_recommendations[topic][tool] += 1

        # Convert to simple dict: topic -> [top tools]
        result = {}
        for topic, tool_counts in topic_tool_recommendations.items():
            # Get top 3 tools for this topic
            top_tools = [tool for tool, _ in tool_counts.most_common(3)]
            if top_tools:
                result[topic] = top_tools

        return result

    def get_learned_routing_rules(self) -> Dict[str, any]:
        """
        Generate routing rules based on feedback analysis.

        Returns:
            Dict with routing recommendations:
            {
                "always_use_scout_for": [list of topics/domains],
                "tool_preferences": {domain: [tools]},
                "time_sensitive_domains": [domains that need fresh data],
                "avoid_cache_for": [patterns that should bypass cache],
            }
        """

        tool_corrections = self.analyze_correction_patterns()
        time_sensitive_domains = self._identify_time_sensitive_domains()

        # Build routing rules
        rules = {
            "tool_preferences": tool_corrections,
            "time_sensitive_domains": list(time_sensitive_domains),
            "always_use_scout_for": [],
            "avoid_cache_for": [],
        }

        # If scout_search appears frequently in corrections, mark topics for scout use
        for topic, tools in tool_corrections.items():
            if "scout_search" in tools:
                rules["always_use_scout_for"].append(topic)

        # Time-sensitive domains should bypass cache
        rules["avoid_cache_for"] = rules["time_sensitive_domains"]

        return rules

    def _identify_time_sensitive_domains(self) -> set:
        """
        Identify domains that require time-sensitive data based on feedback.
        """

        extractions = self.feedback_store.get_all_extractions()

        time_sensitive_domains = set()

        for extraction in extractions:
            if extraction.time_sensitivity_notes:
                # Try to infer domain from corrected facts
                if extraction.corrected_facts and isinstance(extraction.corrected_facts, dict):
                    topic = extraction.corrected_facts.get("topic", "")

                    # Map topics to domains
                    if any(word in topic.lower() for word in ["game", "score", "team"]):
                        time_sensitive_domains.add("sports")
                    elif any(word in topic.lower() for word in ["price", "stock", "bitcoin"]):
                        time_sensitive_domains.add("finance")
                    elif any(word in topic.lower() for word in ["weather", "temperature"]):
                        time_sensitive_domains.add("weather")
                    elif any(word in topic.lower() for word in ["president", "election"]):
                        time_sensitive_domains.add("politics")

        # Default time-sensitive domains (even without feedback)
        time_sensitive_domains.update(["sports", "finance", "weather"])

        return time_sensitive_domains

    def get_tool_recommendation(
        self,
        query: str,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Get tool recommendations for a given query and domain.

        Args:
            query: User query
            domain: Optional domain hint

        Returns:
            List of recommended tool names
        """

        rules = self.get_learned_routing_rules()

        recommendations = []

        # Check domain preferences
        if domain and domain in rules["tool_preferences"]:
            recommendations.extend(rules["tool_preferences"][domain])

        # Check if query is time-sensitive
        query_lower = query.lower()
        time_keywords = ["current", "now", "today", "latest", "recent"]

        is_time_sensitive = any(keyword in query_lower for keyword in time_keywords)

        if is_time_sensitive:
            # Recommend scout_search for time-sensitive queries
            if "scout_search" not in recommendations:
                recommendations.append("scout_search")

        # Check for domain-specific patterns in query
        if any(word in query_lower for word in ["game", "score", "team"]):
            if "scout_search" not in recommendations:
                recommendations.append("scout_search")

        if any(word in query_lower for word in ["price", "stock", "bitcoin"]):
            if "price_query" not in recommendations:
                recommendations.append("price_query")

        if any(word in query_lower for word in ["weather", "temperature", "forecast"]):
            if "weather_current" not in recommendations:
                recommendations.append("weather_current")

        return recommendations[:3]  # Return top 3

    def should_bypass_cache(self, query: str, domain: Optional[str] = None) -> bool:
        """
        Determine if query should bypass cache based on learned patterns.

        Args:
            query: User query
            domain: Optional domain

        Returns:
            True if should bypass cache
        """

        rules = self.get_learned_routing_rules()

        # Check if domain is time-sensitive
        if domain and domain in rules["time_sensitive_domains"]:
            return True

        # Check for time-sensitive keywords
        query_lower = query.lower()
        time_keywords = ["current", "now", "today", "latest", "recent", "live"]

        if any(keyword in query_lower for keyword in time_keywords):
            return True

        # Check avoid_cache patterns
        for pattern in rules["avoid_cache_for"]:
            if pattern in query_lower:
                return True

        return False

    def get_learning_summary(self) -> str:
        """
        Get a human-readable summary of learned patterns.

        Returns:
            Formatted summary string
        """

        tool_perf = self.analyze_tool_performance()
        routing_rules = self.get_learned_routing_rules()

        lines = ["TOOL LEARNING SUMMARY", "=" * 60]

        # Tool performance
        lines.append("\nTool Performance:")
        for tool, stats in sorted(tool_perf.items(), key=lambda x: x[1]["total_uses"], reverse=True):
            lines.append(f"  {tool}:")
            lines.append(f"    Uses: {stats['total_uses']}, Success Rate: {stats['success_rate']:.1%}")

        # Routing rules
        lines.append("\nLearned Routing Rules:")

        if routing_rules["always_use_scout_for"]:
            lines.append(f"  Always use Scout for: {', '.join(routing_rules['always_use_scout_for'])}")

        if routing_rules["time_sensitive_domains"]:
            lines.append(f"  Time-sensitive domains: {', '.join(routing_rules['time_sensitive_domains'])}")

        # Tool preferences by domain
        if routing_rules["tool_preferences"]:
            lines.append("\n  Tool Preferences by Domain:")
            for domain, tools in routing_rules["tool_preferences"].items():
                lines.append(f"    {domain}: {', '.join(tools)}")

        return "\n".join(lines)


# Convenience functions
def get_tool_recommendations(
    query: str,
    domain: Optional[str],
    feedback_store: FeedbackStore
) -> List[str]:
    """Get tool recommendations for a query"""
    engine = ToolLearningEngine(feedback_store)
    return engine.get_tool_recommendation(query, domain)


def should_use_live_data(
    query: str,
    domain: Optional[str],
    feedback_store: FeedbackStore
) -> bool:
    """Determine if query needs live data (bypass cache)"""
    engine = ToolLearningEngine(feedback_store)
    return engine.should_bypass_cache(query, domain)
