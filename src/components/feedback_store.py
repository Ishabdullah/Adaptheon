"""
Production-grade Feedback Storage System for Adaptheon

Stores conversations, turns, feedback events, extractions, and tool use events
in JSON files with atomic writes and file locking for production safety.
"""

import os
import json
import uuid
import fcntl
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class FeedbackType(str, Enum):
    """Types of feedback users can provide"""
    CORRECTION_FACT = "CORRECTION_FACT"
    CORRECTION_TOOL_USE = "CORRECTION_TOOL_USE"
    CORRECTION_LOGIC = "CORRECTION_LOGIC"
    PREFERENCE_STYLE = "PREFERENCE_STYLE"
    PREFERENCE_CAPABILITY = "PREFERENCE_CAPABILITY"
    META_SYSTEM = "META_SYSTEM"


class Severity(str, Enum):
    """Severity levels for feedback"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


@dataclass
class Conversation:
    """A conversation session"""
    id: str
    started_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Turn:
    """A single turn (user or assistant message) in a conversation"""
    id: str
    conversation_id: str
    turn_index: int
    role: str  # "user" or "assistant"
    content: str
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FeedbackEvent:
    """A feedback event from the user"""
    id: str
    conversation_id: str
    target_turn_id: Optional[str]
    raw_text: str
    feedback_types: List[str]
    severity: str
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FeedbackExtraction:
    """Structured extraction from feedback"""
    id: str
    feedback_event_id: str
    corrected_facts: Optional[Dict[str, Any]]
    preferred_tools: List[str]
    style_prefs: Optional[str]
    time_sensitivity_notes: Optional[str]
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ToolUseEvent:
    """A tool use event during a turn"""
    id: str
    conversation_id: str
    turn_id: str
    tool_name: str
    inputs: Dict[str, Any]
    output_summary: str
    success: bool
    error: Optional[str]
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


class FeedbackStore:
    """
    Production-grade feedback storage with atomic writes and file locking.
    Uses JSON files for persistence on Termux/Android.
    """

    def __init__(self, data_dir: str = "data/feedback"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.files = {
            "conversations": os.path.join(data_dir, "conversations.json"),
            "turns": os.path.join(data_dir, "turns.json"),
            "feedback_events": os.path.join(data_dir, "feedback_events.json"),
            "feedback_extractions": os.path.join(data_dir, "feedback_extractions.json"),
            "tool_use_events": os.path.join(data_dir, "tool_use_events.json"),
        }

        # Initialize empty files if they don't exist
        for filepath in self.files.values():
            if not os.path.exists(filepath):
                self._atomic_write(filepath, [])

    def _atomic_write(self, filepath: str, data: List[Dict]):
        """
        Atomic write with file locking for production safety.
        Uses tempfile + rename for atomicity.
        """
        # Write to temp file first
        dir_path = os.path.dirname(filepath)
        fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix=".json.tmp")

        try:
            with os.fdopen(fd, 'w') as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
                # Lock released automatically when file closes

            # Atomic rename
            os.rename(temp_path, filepath)
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e

    def _load(self, filepath: str) -> List[Dict]:
        """Load data from JSON file with error handling"""
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, 'r') as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                data = json.load(f)
                # Lock released automatically
                return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            print(f"[FeedbackStore] WARNING: Corrupted JSON in {filepath}, returning empty list")
            return []
        except Exception as e:
            print(f"[FeedbackStore] ERROR loading {filepath}: {e}")
            return []

    def _save(self, entity_type: str, data: List[Dict]):
        """Save data to JSON file"""
        filepath = self.files.get(entity_type)
        if not filepath:
            raise ValueError(f"Unknown entity type: {entity_type}")
        self._atomic_write(filepath, data)

    def _add_record(self, entity_type: str, record: Dict):
        """Add a single record to an entity collection"""
        data = self._load(self.files[entity_type])
        data.append(record)
        self._save(entity_type, data)

    # ========== Conversation Management ==========

    def create_conversation(self, metadata: Optional[Dict] = None) -> Conversation:
        """Create a new conversation"""
        conv = Conversation(
            id=str(uuid.uuid4()),
            started_at=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {}
        )
        self._add_record("conversations", conv.to_dict())
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID"""
        convs = self._load(self.files["conversations"])
        for c in convs:
            if c["id"] == conversation_id:
                return Conversation(**c)
        return None

    # ========== Turn Management ==========

    def add_turn(self, conversation_id: str, role: str, content: str, turn_index: int) -> Turn:
        """Add a turn to a conversation"""
        turn = Turn(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            turn_index=turn_index,
            role=role,
            content=content,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        self._add_record("turns", turn.to_dict())
        return turn

    def get_turns(self, conversation_id: str) -> List[Turn]:
        """Get all turns for a conversation"""
        turns = self._load(self.files["turns"])
        results = [Turn(**t) for t in turns if t["conversation_id"] == conversation_id]
        results.sort(key=lambda t: t.turn_index)
        return results

    def get_last_assistant_turn(self, conversation_id: str) -> Optional[Turn]:
        """Get the most recent assistant turn"""
        turns = self.get_turns(conversation_id)
        assistant_turns = [t for t in turns if t.role == "assistant"]
        return assistant_turns[-1] if assistant_turns else None

    # ========== Feedback Event Management ==========

    def add_feedback_event(
        self,
        conversation_id: str,
        target_turn_id: Optional[str],
        raw_text: str,
        feedback_types: List[str],
        severity: str = "moderate"
    ) -> FeedbackEvent:
        """Add a feedback event"""
        event = FeedbackEvent(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            target_turn_id=target_turn_id,
            raw_text=raw_text,
            feedback_types=feedback_types,
            severity=severity,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        self._add_record("feedback_events", event.to_dict())
        return event

    def get_feedback_events(self, conversation_id: str) -> List[FeedbackEvent]:
        """Get all feedback events for a conversation"""
        events = self._load(self.files["feedback_events"])
        return [FeedbackEvent(**e) for e in events if e["conversation_id"] == conversation_id]

    # ========== Feedback Extraction Management ==========

    def add_feedback_extraction(
        self,
        feedback_event_id: str,
        corrected_facts: Optional[Dict] = None,
        preferred_tools: Optional[List[str]] = None,
        style_prefs: Optional[str] = None,
        time_sensitivity_notes: Optional[str] = None
    ) -> FeedbackExtraction:
        """Add structured feedback extraction"""
        extraction = FeedbackExtraction(
            id=str(uuid.uuid4()),
            feedback_event_id=feedback_event_id,
            corrected_facts=corrected_facts,
            preferred_tools=preferred_tools or [],
            style_prefs=style_prefs,
            time_sensitivity_notes=time_sensitivity_notes,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        self._add_record("feedback_extractions", extraction.to_dict())
        return extraction

    def get_extractions_for_event(self, feedback_event_id: str) -> List[FeedbackExtraction]:
        """Get extractions for a feedback event"""
        extractions = self._load(self.files["feedback_extractions"])
        return [FeedbackExtraction(**e) for e in extractions if e["feedback_event_id"] == feedback_event_id]

    def get_all_extractions(self, conversation_id: Optional[str] = None) -> List[FeedbackExtraction]:
        """Get all feedback extractions, optionally filtered by conversation"""
        extractions = self._load(self.files["feedback_extractions"])
        all_extractions = [FeedbackExtraction(**e) for e in extractions]

        if conversation_id:
            # Filter by conversation via feedback events
            events = self.get_feedback_events(conversation_id)
            event_ids = {e.id for e in events}
            return [ex for ex in all_extractions if ex.feedback_event_id in event_ids]

        return all_extractions

    # ========== Tool Use Event Management ==========

    def add_tool_use_event(
        self,
        conversation_id: str,
        turn_id: str,
        tool_name: str,
        inputs: Dict,
        output_summary: str,
        success: bool,
        error: Optional[str] = None
    ) -> ToolUseEvent:
        """Add a tool use event"""
        event = ToolUseEvent(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            turn_id=turn_id,
            tool_name=tool_name,
            inputs=inputs,
            output_summary=output_summary,
            success=success,
            error=error,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        self._add_record("tool_use_events", event.to_dict())
        return event

    def get_tool_use_events(self, conversation_id: Optional[str] = None) -> List[ToolUseEvent]:
        """Get tool use events, optionally filtered by conversation"""
        events = self._load(self.files["tool_use_events"])
        if conversation_id:
            return [ToolUseEvent(**e) for e in events if e["conversation_id"] == conversation_id]
        return [ToolUseEvent(**e) for e in events]

    # ========== Convenience Methods ==========

    def save_feedback(
        self,
        conversation_id: str,
        target_turn_id: Optional[str],
        raw_text: str,
        feedback_types: List[str],
        severity: str,
        corrected_facts: Optional[Dict] = None,
        preferred_tools: Optional[List[str]] = None,
        style_prefs: Optional[str] = None,
        time_sensitivity_notes: Optional[str] = None
    ) -> tuple[FeedbackEvent, FeedbackExtraction]:
        """
        Convenience method to save both feedback event and extraction in one call.
        Returns (event, extraction) tuple.
        """
        event = self.add_feedback_event(
            conversation_id=conversation_id,
            target_turn_id=target_turn_id,
            raw_text=raw_text,
            feedback_types=feedback_types,
            severity=severity
        )

        extraction = self.add_feedback_extraction(
            feedback_event_id=event.id,
            corrected_facts=corrected_facts,
            preferred_tools=preferred_tools,
            style_prefs=style_prefs,
            time_sensitivity_notes=time_sensitivity_notes
        )

        return event, extraction

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about stored data"""
        return {
            "conversations": len(self._load(self.files["conversations"])),
            "turns": len(self._load(self.files["turns"])),
            "feedback_events": len(self._load(self.files["feedback_events"])),
            "feedback_extractions": len(self._load(self.files["feedback_extractions"])),
            "tool_use_events": len(self._load(self.files["tool_use_events"])),
        }
