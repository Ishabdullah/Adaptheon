#!/usr/bin/env python3
"""
Test that temporal queries actually route to external sources, not base LLM
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from components.llm_interface import LanguageSystem
from components.hrm import HierarchicalReasoningMachine

def test_temporal_routing():
    """Test that time-sensitive queries trigger TRIGGER_SCOUT action"""

    print("="*80)
    print("TEMPORAL ROUTING TEST")
    print("="*80)

    llm = LanguageSystem()
    hrm = HierarchicalReasoningMachine()

    test_cases = [
        ("who is the current president of the united states", True, "TRIGGER_SCOUT"),
        ("what is the current price of bitcoin", True, "PRICE_QUERY"),
        ("what is the weather today", True, "WEATHER_QUERY"),
        ("who was the president in 1990", False, "CONVERSE"),  # Historical - can use base LLM
        ("what is bitcoin", False, "TRIGGER_SCOUT"),  # Definition - search external sources for accuracy
        ("tell me a joke", False, "CONVERSE"),  # Non-factual - can use base LLM
    ]

    passed = 0
    failed = 0

    for query, should_be_temporal, expected_action in test_cases:
        print(f"\n{'='*80}")
        print(f"Query: '{query}'")
        print(f"Expected: time_sensitive={should_be_temporal}, action={expected_action}")

        # Parse intent
        intent = llm.parse_intent(query)

        # Process through HRM
        result = hrm.process(intent, {})

        action = result.get("action")
        time_sensitive = result.get("time_sensitive", False)

        print(f"Got: time_sensitive={time_sensitive}, action={action}")

        # Check if temporal flag is correct
        temporal_ok = time_sensitive == should_be_temporal

        # Check if action is correct
        action_ok = action == expected_action

        if temporal_ok and action_ok:
            print("✓ PASS")
            passed += 1
        else:
            print("✗ FAIL")
            if not temporal_ok:
                print(f"  Temporal detection mismatch: expected {should_be_temporal}, got {time_sensitive}")
            if not action_ok:
                print(f"  Action mismatch: expected {expected_action}, got {action}")
            failed += 1

    print(f"\n{'='*80}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*80}")

    return failed == 0

if __name__ == "__main__":
    success = test_temporal_routing()
    sys.exit(0 if success else 1)
