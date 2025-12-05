"""
Migration utility to convert existing disputes.json to new FeedbackStore format.

Reads data/memory/disputes.json and creates corresponding feedback events
and extractions in the new FeedbackStore.
"""

import os
import json
from feedback_store import FeedbackStore, FeedbackType, Severity


def migrate_disputes_to_feedback_store(
    disputes_path: str = "data/memory/disputes.json",
    feedback_store: FeedbackStore = None
):
    """
    Migrate existing disputes.json to FeedbackStore.

    Each dispute becomes:
    - A synthetic conversation (one per dispute)
    - Two turns: assistant answer + user correction
    - A feedback event with CORRECTION_FACT type
    - A feedback extraction with corrected facts
    """

    if not os.path.exists(disputes_path):
        print(f"[Migration] No disputes file found at {disputes_path}")
        return

    if feedback_store is None:
        feedback_store = FeedbackStore()

    # Load existing disputes
    with open(disputes_path, 'r') as f:
        try:
            disputes = json.load(f)
        except json.JSONDecodeError:
            print(f"[Migration] ERROR: Could not parse {disputes_path}")
            return

    print(f"[Migration] Found {len(disputes)} disputes to migrate")

    migrated_count = 0
    for dispute in disputes:
        try:
            # Create a synthetic conversation for this dispute
            conv = feedback_store.create_conversation(metadata={
                "source": "migrated_from_disputes",
                "topic": dispute.get("topic", "unknown")
            })

            # Create assistant turn (the incorrect answer)
            old_summary = dispute.get("old_summary", "")
            assistant_turn = feedback_store.add_turn(
                conversation_id=conv.id,
                role="assistant",
                content=old_summary[:500],  # Truncate if too long
                turn_index=0
            )

            # Create user turn (the correction)
            user_correction = dispute.get("user_correction", "")
            user_turn = feedback_store.add_turn(
                conversation_id=conv.id,
                role="user",
                content=user_correction,
                turn_index=1
            )

            # Determine severity based on presence of "wrong" or similar strong words
            severity = "major" if any(word in user_correction.lower() for word in ["wrong", "incorrect", "false"]) else "moderate"

            # Create feedback event
            event, extraction = feedback_store.save_feedback(
                conversation_id=conv.id,
                target_turn_id=assistant_turn.id,
                raw_text=user_correction,
                feedback_types=[FeedbackType.CORRECTION_FACT],
                severity=severity,
                corrected_facts={
                    "topic": dispute.get("topic", ""),
                    "old_summary": dispute.get("old_summary", "")[:200],
                    "scout_result": dispute.get("scout_summary", "")[:200],
                    "scout_source": dispute.get("scout_source", ""),
                    "scout_confidence": dispute.get("scout_confidence", 0.0),
                },
                preferred_tools=["scout_search"] if dispute.get("scout_status") == "FOUND" else [],
                time_sensitivity_notes=None
            )

            migrated_count += 1
            print(f"[Migration] Migrated dispute #{migrated_count}: topic='{dispute.get('topic', '')[:30]}'")

        except Exception as e:
            print(f"[Migration] ERROR migrating dispute: {e}")
            continue

    print(f"[Migration] Successfully migrated {migrated_count}/{len(disputes)} disputes")
    print(f"[Migration] Stats: {feedback_store.get_stats()}")


if __name__ == "__main__":
    print("="*80)
    print("ADAPTHEON DISPUTES MIGRATION")
    print("="*80)

    store = FeedbackStore()
    print(f"\nBefore migration: {store.get_stats()}")

    migrate_disputes_to_feedback_store(feedback_store=store)

    print(f"\nAfter migration: {store.get_stats()}")
    print("\nMigration complete!")
