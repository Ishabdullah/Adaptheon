# Feedback System Integration Guide

## Overview

The feedback system has been implemented with the following components:

### Core Modules

1. **FeedbackStore** (`src/components/feedback_store.py`)
   - JSON-based storage with atomic writes and file locking
   - Stores: conversations, turns, feedback_events, feedback_extractions, tool_use_events
   - Production-safe for Termux/Android

2. **FeedbackDetector** (`src/components/feedback_detector.py`)
   - Pattern-based detection of 6 feedback types
   - Classifies severity (minor/moderate/major)
   - Extracts structured data (corrected facts, preferred tools, style prefs)

3. **FeedbackContext** (`src/components/feedback_context.py`)
   - Retrieves relevant feedback for current query
   - Builds context snippets for LLM injection
   - Domain-specific filtering

4. **ToolLearningEngine** (`src/components/tool_learning.py`)
   - Analyzes feedback patterns
   - Learns routing rules (when to use scout, which tools for domains)
   - Recommends cache bypass for time-sensitive queries

5. **Migration Utility** (`src/components/migrate_disputes.py`)
   - Converts existing disputes.json to new format
   - Preserves historical feedback data

## Integration into MetaCognitiveCore

### Required Changes

#### 1. Add to `__init__`:
```python
from components.feedback_store import FeedbackStore
from components.feedback_detector import FeedbackDetector
from components.feedback_context import get_relevant_feedback, build_feedback_context_snippet
from components.tool_learning import ToolLearningEngine
import uuid
import logging

class MetaCognitiveCore:
    def __init__(self):
        # ... existing init ...

        # Feedback system
        self.feedback_store = FeedbackStore()
        self.feedback_detector = FeedbackDetector()
        self.tool_learning = ToolLearningEngine(self.feedback_store)

        # Conversation tracking
        self.current_conversation = None
        self.turn_counter = 0

        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('data/logs/adaptheon.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Adaptheon')
```

#### 2. Modify `run_cycle`:

```python
def run_cycle(self, user_input):
    # Create conversation if needed
    if not self.current_conversation:
        self.current_conversation = self.feedback_store.create_conversation(
            metadata={"device": "termux", "model": "qwen-1.5b"}
        )
        self.turn_counter = 0
        self.logger.info(f"Started conversation {self.current_conversation.id}")

    # Add user turn
    user_turn = self.feedback_store.add_turn(
        conversation_id=self.current_conversation.id,
        role="user",
        content=user_input,
        turn_index=self.turn_counter
    )
    self.turn_counter += 1

    # Get conversation history for feedback detection
    recent_turns = self.feedback_store.get_turns(self.current_conversation.id)

    # FEEDBACK DETECTION
    feedback_detection = self.feedback_detector.detect_feedback(user_input, recent_turns)
    if feedback_detection and feedback_detection.is_feedback:
        self.logger.info(f"Feedback detected: types={feedback_detection.feedback_types}, "
                        f"severity={feedback_detection.severity}")

        # Save feedback
        event, extraction = self.feedback_store.save_feedback(
            conversation_id=self.current_conversation.id,
            target_turn_id=feedback_detection.target_turn_id,
            raw_text=user_input,
            feedback_types=feedback_detection.feedback_types,
            severity=feedback_detection.severity,
            corrected_facts=feedback_detection.corrected_facts,
            preferred_tools=feedback_detection.preferred_tools,
            style_prefs=feedback_detection.style_prefs,
            time_sensitivity_notes=feedback_detection.time_sensitivity_notes
        )

        self.logger.info(f"Saved feedback event {event.id[:8]}")

    # GET RELEVANT FEEDBACK FOR CONTEXT
    relevant_feedback = get_relevant_feedback(
        conversation_id=self.current_conversation.id,
        current_query=user_input,
        feedback_store=self.feedback_store,
        max_results=5
    )

    feedback_context = build_feedback_context_snippet(relevant_feedback, max_length=500)

    if feedback_context:
        self.logger.info(f"Injecting feedback context ({len(relevant_feedback)} items)")

    # Parse intent (existing)
    intent = self.llm.parse_intent(user_input)
    context = self.memory.get_context()
    logic_output = self.hrm.process(intent, context)

    action = logic_output.get("action")
    time_sensitive = logic_output.get("time_sensitive", False)

    # Tool recommendation from learning
    domain = logic_output.get("domain")  # If HRM provides domain
    tool_recommendations = self.tool_learning.get_tool_recommendation(user_input, domain)

    if tool_recommendations:
        self.logger.info(f"Tool recommendations: {tool_recommendations}")

    # ... existing action handling ...

    # INJECT FEEDBACK CONTEXT INTO LLM CALLS
    # For all LLM calls, prepend feedback_context to system instruction:

    if action == "TRIGGER_SCOUT":
        # Log tool use
        tool_event_id = str(uuid.uuid4())

        # ... existing scout logic ...

        # Log tool use event
        self.feedback_store.add_tool_use_event(
            conversation_id=self.current_conversation.id,
            turn_id=user_turn.id,
            tool_name="scout_search",
            inputs={"topic": topic},
            output_summary=scout_result.get("summary", "")[:200],
            success=scout_result["status"] == "FOUND",
            error=None if scout_result["status"] == "FOUND" else "NOT_FOUND"
        )

        # Inject feedback context when rewriting
        system_instruction_with_feedback = feedback_context + get_temporal_system_hint() if time_sensitive else feedback_context

        rewritten = self.llm.rewrite_from_sources(
            question=topic,
            raw_summary=scout_result["summary"],
            source_label=scout_result["source"],
            temporal_hint=system_instruction_with_feedback
        )
        final_response = rewritten

    # Similar for PRICE_QUERY, WEATHER_QUERY, etc.

    # Add assistant turn
    assistant_turn = self.feedback_store.add_turn(
        conversation_id=self.current_conversation.id,
        role="assistant",
        content=final_response,
        turn_index=self.turn_counter
    )
    self.turn_counter += 1

    # Existing memory storage
    self.memory.add_episodic(user_input, final_response)

    return final_response
```

### Key Integration Points

1. **Conversation Tracking**: Create conversation on first turn, track turn_counter
2. **Feedback Detection**: After user input, check for feedback patterns
3. **Feedback Storage**: Save detected feedback with structured extraction
4. **Context Injection**: Retrieve relevant feedback and inject into LLM system prompts
5. **Tool Use Logging**: Log all tool calls (scout, price, weather, etc.)
6. **Learning Integration**: Use tool recommendations from learned patterns

### Testing the Integration

Run:
```bash
cd ~/Adaptheon
python src/meta_core.py
```

Test feedback:
```
> What's the price of bitcoin?
[Assistant answers]
> That's wrong, bitcoin is actually $95,000
[System detects CORRECTION_FACT feedback, saves it]
> What's the price of ethereum?
[System uses feedback context: "User previously corrected bitcoin prices, use live API"]
```

### Logging

All feedback events are logged to `data/logs/adaptheon.log`:
- Feedback detection events
- Feedback context injection
- Tool use events
- Learning recommendations

### Storage

All data persists in `data/feedback/*.json`:
- conversations.json
- turns.json
- feedback_events.json
- feedback_extractions.json
- tool_use_events.json

### Migration

To migrate existing disputes:
```bash
cd ~/Adaptheon/src/components
python migrate_disputes.py
```

## Production Considerations

1. **File Locking**: Atomic writes with fcntl for concurrent safety
2. **Error Handling**: Graceful degradation if feedback system fails
3. **Performance**: Feedback detection is pattern-based (no ML inference overhead)
4. **Storage**: JSON files grow linearly; consider archiving old conversations periodically
5. **Privacy**: All data stored locally on device (Termux/Android)

## Future Enhancements

1. Add graph-based feedback relationships
2. Implement feedback summarization for very long conversations
3. Add feedback export/import for backup
4. Implement user-configurable feedback sensitivity
