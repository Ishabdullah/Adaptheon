"""
Feedback Detection Module for Adaptheon

Detects when users provide corrections, preferences, or meta-system feedback.
Uses pattern matching and heuristics (no external ML needed).
"""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from feedback_store import FeedbackType, Severity, Turn


@dataclass
class FeedbackDetection:
    """Result of feedback detection"""
    is_feedback: bool
    feedback_types: List[str]
    severity: str
    target_turn_id: Optional[str]
    corrected_facts: Optional[Dict[str, Any]]
    preferred_tools: List[str]
    style_prefs: Optional[str]
    time_sensitivity_notes: Optional[str]
    confidence: float  # 0.0-1.0


class FeedbackDetector:
    """
    Detects and classifies user feedback using pattern matching.
    """

    # Pattern sets for different feedback types
    CORRECTION_FACT_PATTERNS = [
        r"that'?s? (wrong|incorrect|not right|false|inaccurate)",
        r"(actually|in fact|really|truth is),?\s+",
        r"(no|nope|wrong),?\s+(the |it |that )",
        r"you'?re? (wrong|incorrect|mistaken)",
        r"(correction|fix):?\s+",
        r"(should be|is actually|was actually|correct answer is)",
        r"(not|isn'?t|wasn'?t|aren'?t|weren'?t)\s+\w+,?\s+(it'?s?|they'?re?|the)",
    ]

    CORRECTION_TOOL_PATTERNS = [
        r"you should (have )?(use[d]?|check[ed]?|search[ed]?|look[ed]?|call[ed]?)",
        r"(why didn'?t you|you didn'?t|you never)\s+(use|check|search|look|call)",
        r"(use|try|check)\s+(the )?(web|internet|search|scout|espn|api|tool)",
        r"(should have|could have)\s+\w+\s+(scout|search|tool|api|espn|wikipedia)",
        r"next time\s+(use|check|try|search|call)",
        r"(always|must|need to)\s+(use|check|search|call)\s+\w+\s+(for|when|to)",
    ]

    CORRECTION_LOGIC_PATTERNS = [
        r"that doesn'?t make sense",
        r"(your |the )?logic is (wrong|flawed|incorrect|bad)",
        r"that'?s? (illogical|contradictory|inconsistent)",
        r"you contradicted yourself",
        r"(doesn'?t|don'?t) follow",
    ]

    PREFERENCE_STYLE_PATTERNS = [
        r"(please |can you )?(be more|make it|keep (it |your answers?))\s+(concise|brief|short|detailed|verbose|simple)",
        r"(use|don'?t use|avoid|prefer)\s+(bullet points|bullets|lists|paragraphs|sentences)",
        r"(too |very )?(long|short|verbose|wordy|terse)",
        r"(i |we )?(want|need|prefer|like)\s+(shorter|longer|more|less|simpler|detailed)",
        r"(keep|make)\s+(answers?|responses?|it)\s+\w+",
    ]

    PREFERENCE_CAPABILITY_PATTERNS = [
        r"(don'?t|never|always|must)\s+(use|do|say|mention|include|show)",
        r"(i|we)\s+(want|need|prefer|like)\s+you to",
        r"from now on",
        r"in the future",
        r"(remember|keep in mind) (that |to )?",
    ]

    META_SYSTEM_PATTERNS = [
        r"(you'?re?|this system is|adaptheon is)\s+(slow|fast|good|bad|broken|great|helpful)",
        r"(bug|error|issue|problem) (with|in) (you|the system|adaptheon)",
        r"(feature request|suggestion):?",
        r"(could|should|would) be (better|improved|enhanced)",
    ]

    # Tool name patterns
    TOOL_PATTERNS = {
        "scout_search": [r"(scout|knowledge scout|search)"],
        "price_query": [r"(price|pricing|cost|value)\s+(service|api|query|tool|check)"],
        "weather_current": [r"(weather|temperature|forecast)\s+(service|api|check)"],
        "espn": [r"(espn|sports api|game scores?)"],
        "wikipedia": [r"(wikipedia|wiki)"],
        "web_search": [r"(web search|google|internet search|online search)"],
        "arxiv": [r"(arxiv|academic papers?)"],
        "github": [r"(github|repositories|repos)"],
    ]

    # Time sensitivity patterns
    TIME_SENSITIVITY_PATTERNS = [
        r"(current|now|today|latest|recent|live|real-?time)",
        r"(always|must)\s+\w+\s+(current|fresh|live|latest|up-to-date)",
        r"(never|don'?t)\s+\w+\s+(old|stale|cached|outdated)",
    ]

    def __init__(self):
        # Compile patterns for performance
        self.correction_fact_re = [re.compile(p, re.IGNORECASE) for p in self.CORRECTION_FACT_PATTERNS]
        self.correction_tool_re = [re.compile(p, re.IGNORECASE) for p in self.CORRECTION_TOOL_PATTERNS]
        self.correction_logic_re = [re.compile(p, re.IGNORECASE) for p in self.CORRECTION_LOGIC_PATTERNS]
        self.preference_style_re = [re.compile(p, re.IGNORECASE) for p in self.PREFERENCE_STYLE_PATTERNS]
        self.preference_capability_re = [re.compile(p, re.IGNORECASE) for p in self.PREFERENCE_CAPABILITY_PATTERNS]
        self.meta_system_re = [re.compile(p, re.IGNORECASE) for p in self.META_SYSTEM_PATTERNS]
        self.time_sensitivity_re = [re.compile(p, re.IGNORECASE) for p in self.TIME_SENSITIVITY_PATTERNS]

    def detect_feedback(
        self,
        user_text: str,
        conversation_turns: List[Turn]
    ) -> Optional[FeedbackDetection]:
        """
        Detect if user_text contains feedback and classify it.

        Args:
            user_text: The user's message
            conversation_turns: Recent conversation turns for context

        Returns:
            FeedbackDetection if feedback detected, None otherwise
        """

        text_lower = user_text.lower()
        feedback_types = []
        confidence_scores = []

        # Check each feedback type
        if self._matches_patterns(self.correction_fact_re, text_lower):
            feedback_types.append(FeedbackType.CORRECTION_FACT)
            confidence_scores.append(0.9)

        if self._matches_patterns(self.correction_tool_re, text_lower):
            feedback_types.append(FeedbackType.CORRECTION_TOOL_USE)
            confidence_scores.append(0.85)

        if self._matches_patterns(self.correction_logic_re, text_lower):
            feedback_types.append(FeedbackType.CORRECTION_LOGIC)
            confidence_scores.append(0.8)

        if self._matches_patterns(self.preference_style_re, text_lower):
            feedback_types.append(FeedbackType.PREFERENCE_STYLE)
            confidence_scores.append(0.75)

        if self._matches_patterns(self.preference_capability_re, text_lower):
            feedback_types.append(FeedbackType.PREFERENCE_CAPABILITY)
            confidence_scores.append(0.7)

        if self._matches_patterns(self.meta_system_re, text_lower):
            feedback_types.append(FeedbackType.META_SYSTEM)
            confidence_scores.append(0.6)

        # No feedback detected
        if not feedback_types:
            return None

        # Determine severity
        severity = self._determine_severity(text_lower, feedback_types)

        # Resolve target turn
        target_turn_id = self._resolve_target_turn(user_text, conversation_turns)

        # Extract structured data
        corrected_facts = self._extract_corrected_facts(user_text) if FeedbackType.CORRECTION_FACT in feedback_types else None
        preferred_tools = self._extract_tools(user_text) if FeedbackType.CORRECTION_TOOL_USE in feedback_types else []
        style_prefs = self._extract_style_prefs(user_text) if FeedbackType.PREFERENCE_STYLE in feedback_types else None
        time_sensitivity_notes = self._extract_time_sensitivity(user_text)

        # Compute confidence (average of all matched pattern types)
        confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

        return FeedbackDetection(
            is_feedback=True,
            feedback_types=feedback_types,
            severity=severity,
            target_turn_id=target_turn_id,
            corrected_facts=corrected_facts,
            preferred_tools=preferred_tools,
            style_prefs=style_prefs,
            time_sensitivity_notes=time_sensitivity_notes,
            confidence=confidence
        )

    def _matches_patterns(self, patterns: List[re.Pattern], text: str) -> bool:
        """Check if text matches any pattern in the list"""
        return any(p.search(text) for p in patterns)

    def _determine_severity(self, text: str, feedback_types: List[str]) -> str:
        """Determine severity based on language and type"""
        # Strong negative words = major
        if any(word in text for word in ["wrong", "completely wrong", "totally wrong", "false", "incorrect", "broken", "terrible", "awful"]):
            return Severity.MAJOR

        # Meta system issues = moderate
        if FeedbackType.META_SYSTEM in feedback_types:
            return Severity.MODERATE

        # Corrections = moderate by default
        if any(t.startswith("CORRECTION") for t in feedback_types):
            return Severity.MODERATE

        # Preferences = minor
        return Severity.MINOR

    def _resolve_target_turn(self, user_text: str, turns: List[Turn]) -> Optional[str]:
        """
        Resolve which turn the user is referring to.

        Heuristics:
        1. If text contains "that" or "last", assume previous assistant turn
        2. If text contains quoted text, fuzzy match against recent turns
        3. Default to most recent assistant turn
        """

        text_lower = user_text.lower()

        # Get recent assistant turns (last 5)
        assistant_turns = [t for t in turns if t.role == "assistant"][-5:]

        if not assistant_turns:
            return None

        # Heuristic 1: "that", "last answer", etc.
        if any(phrase in text_lower for phrase in ["that's", "that is", "last answer", "your answer", "you said"]):
            return assistant_turns[-1].id if assistant_turns else None

        # Heuristic 2: Quoted text matching
        # Look for text in quotes
        quoted_matches = re.findall(r'["\'](.+?)["\']', user_text)
        if quoted_matches:
            for quote in quoted_matches:
                for turn in reversed(assistant_turns):
                    if quote.lower() in turn.content.lower():
                        return turn.id

        # Default: most recent assistant turn
        return assistant_turns[-1].id if assistant_turns else None

    def _extract_corrected_facts(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract corrected facts from text"""
        # Look for "actually X" or "is actually Y" patterns
        patterns = [
            r"(actually|in fact|really|truth is),?\s+(.+?)(?:\.|$)",
            r"(should be|is actually|correct answer is|it'?s?)\s+(.+?)(?:\.|$)",
        ]

        corrections = {}
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                corrections["new_value"] = match.group(2).strip()

        return corrections if corrections else None

    def _extract_tools(self, text: str) -> List[str]:
        """Extract tool names mentioned in feedback"""
        mentioned_tools = []

        for tool_name, patterns in self.TOOL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    mentioned_tools.append(tool_name)
                    break

        return mentioned_tools

    def _extract_style_prefs(self, text: str) -> Optional[str]:
        """Extract style preferences as free text"""
        text_lower = text.lower()

        # Extract preference hints
        prefs = []

        if any(word in text_lower for word in ["short", "brief", "concise", "terse"]):
            prefs.append("prefer shorter responses")

        if any(word in text_lower for word in ["long", "detailed", "verbose", "elaborate"]):
            prefs.append("prefer detailed responses")

        if "bullet" in text_lower:
            if "don't" in text_lower or "avoid" in text_lower:
                prefs.append("avoid bullet points")
            else:
                prefs.append("use bullet points")

        if "simple" in text_lower:
            prefs.append("use simple language")

        return "; ".join(prefs) if prefs else None

    def _extract_time_sensitivity(self, text: str) -> Optional[str]:
        """Extract time sensitivity notes"""
        if self._matches_patterns(self.time_sensitivity_re, text):
            # Extract relevant phrases
            notes = []

            if re.search(r"(always|must)\s+\w+\s+(current|fresh|live|latest)", text, re.IGNORECASE):
                notes.append("User expects always-current data")

            if re.search(r"(never|don'?t)\s+\w+\s+(old|stale|cached|outdated)", text, re.IGNORECASE):
                notes.append("User rejects cached/outdated data")

            if any(word in text.lower() for word in ["real-time", "live", "current"]):
                notes.append("User requires real-time/live data")

            return "; ".join(notes) if notes else "User mentioned time-sensitive data requirements"

        return None


# Convenience function for direct use
def detect_feedback(user_text: str, conversation_turns: List[Turn]) -> Optional[FeedbackDetection]:
    """
    Detect feedback in user text.

    Args:
        user_text: User's message
        conversation_turns: Recent conversation history

    Returns:
        FeedbackDetection if feedback found, None otherwise
    """
    detector = FeedbackDetector()
    return detector.detect_feedback(user_text, conversation_turns)
