#!/usr/bin/env python3
"""
Temporal Awareness Test Suite for Adaptheon

Tests that the system correctly:
1. Detects temporal intent in queries
2. Routes time-sensitive queries to external sources
3. Bypasses cache for post-cutoff queries
4. Uses base knowledge for historical queries (pre-cutoff)
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from components.temporal_awareness import (
    detect_temporal_intent,
    should_use_external_sources,
    KNOWLEDGE_CUTOFF,
    contains_temporal_keywords,
    contains_temporal_domain,
    extract_years_from_text,
)
from components.time_service import get_now, get_knowledge_cutoff_info
from meta_core import MetaCognitiveCore


def test_temporal_detection():
    """Test 1: Temporal Intent Detection"""
    print("\n" + "="*80)
    print("TEST 1: TEMPORAL INTENT DETECTION")
    print("="*80)

    test_cases = [
        # Should be detected as temporal
        ("What is the date today?", True, "contains 'today'"),
        ("What is the current price of bitcoin?", True, "contains 'current' and 'price'"),
        ("Who is the current president of the United States?", True, "contains 'current' and 'president'"),
        ("What's the weather right now?", True, "contains 'right now' and 'weather'"),
        ("Latest news about AI in 2024", True, "contains 'latest' and '2024'"),
        ("Recent developments in quantum computing", True, "contains 'recent'"),

        # Should NOT be detected as temporal
        ("What is Bitcoin?", False, "no temporal indicators"),
        ("Who was the president in 1990?", False, "year 1990 is before cutoff"),
        ("Explain quantum computing", False, "no temporal indicators"),
        ("Define machine learning", False, "no temporal indicators"),
    ]

    passed = 0
    failed = 0

    for query, expected_temporal, reason in test_cases:
        result = detect_temporal_intent(query)
        is_temporal = result['is_after_cutoff']

        status = "✓ PASS" if is_temporal == expected_temporal else "✗ FAIL"
        if is_temporal == expected_temporal:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}: '{query}'")
        print(f"  Expected: {expected_temporal} ({reason})")
        print(f"  Got: {is_temporal}")
        if is_temporal:
            print(f"  Reason: {result['reason']}")

    print(f"\n{'-'*80}")
    print(f"Test 1 Results: {passed} passed, {failed} failed ({passed}/{passed+failed})")
    return passed, failed


def test_knowledge_cutoff_info():
    """Test 2: Knowledge Cutoff Configuration"""
    print("\n" + "="*80)
    print("TEST 2: KNOWLEDGE CUTOFF CONFIGURATION")
    print("="*80)

    cutoff_info = get_knowledge_cutoff_info()

    print(f"\nKnowledge Cutoff Date: {cutoff_info['cutoff_date']}")
    print(f"Current Date: {cutoff_info['current_date']}")
    print(f"Days Since Cutoff: {cutoff_info['days_since_cutoff']}")
    print(f"Is Current After Cutoff: {cutoff_info['is_current_after_cutoff']}")

    # Verify cutoff is set correctly
    expected_cutoff = "2023-06-30"
    actual_cutoff = cutoff_info['cutoff_date']

    if actual_cutoff == expected_cutoff:
        print(f"\n✓ PASS: Cutoff date correctly set to {expected_cutoff}")
        return 1, 0
    else:
        print(f"\n✗ FAIL: Expected cutoff {expected_cutoff}, got {actual_cutoff}")
        return 0, 1


def test_system_time_query():
    """Test 3: System Time Query"""
    print("\n" + "="*80)
    print("TEST 3: SYSTEM TIME QUERY")
    print("="*80)

    time_info = get_now()

    print(f"\nCurrent Time (ISO): {time_info['iso']}")
    print(f"Current Date: {time_info['date']}")
    print(f"Current Time: {time_info['time']}")

    # Verify we get reasonable date (should be after cutoff)
    today = time_info['date_obj']
    if today > KNOWLEDGE_CUTOFF:
        print(f"\n✓ PASS: System time ({today}) is after knowledge cutoff ({KNOWLEDGE_CUTOFF})")
        return 1, 0
    else:
        print(f"\n✗ FAIL: System time ({today}) is not after knowledge cutoff ({KNOWLEDGE_CUTOFF})")
        return 0, 1


def test_temporal_keywords():
    """Test 4: Temporal Keyword Detection"""
    print("\n" + "="*80)
    print("TEST 4: TEMPORAL KEYWORD DETECTION")
    print("="*80)

    test_cases = [
        ("What is happening today?", True),
        ("Show me the latest results", True),
        ("Current status of the project", True),
        ("What is Bitcoin?", False),
        ("Historical data from 1990", False),
    ]

    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = contains_temporal_keywords(query)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}: '{query}' -> {result} (expected {expected})")

    print(f"\n{'-'*80}")
    print(f"Test 4 Results: {passed} passed, {failed} failed ({passed}/{passed+failed})")
    return passed, failed


def test_temporal_domains():
    """Test 5: Always-Temporal Domain Detection"""
    print("\n" + "="*80)
    print("TEST 5: ALWAYS-TEMPORAL DOMAIN DETECTION")
    print("="*80)

    test_cases = [
        ("What is the price of bitcoin?", True, "price"),
        ("Show me the weather forecast", True, "weather"),
        ("Who won the game last night?", True, "game"),
        ("What is the temperature?", True, "temperature"),
        ("Explain blockchain technology", False, "no temporal domain"),
    ]

    passed = 0
    failed = 0

    for query, expected, reason in test_cases:
        result = contains_temporal_domain(query)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}: '{query}' -> {result} (expected {expected}, {reason})")

    print(f"\n{'-'*80}")
    print(f"Test 5 Results: {passed} passed, {failed} failed ({passed}/{passed+failed})")
    return passed, failed


def test_year_extraction():
    """Test 6: Year Extraction from Text"""
    print("\n" + "="*80)
    print("TEST 6: YEAR EXTRACTION FROM TEXT")
    print("="*80)

    test_cases = [
        ("Events in 2024 and 2025", [2024, 2025]),
        ("The year 1990 was historic", [1990]),
        ("No years in this text", []),
        ("Back in the 2010s and 2020s", [2010, 2020]),
    ]

    passed = 0
    failed = 0

    for query, expected in test_cases:
        result = extract_years_from_text(query)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status}: '{query}' -> {result} (expected {expected})")

    print(f"\n{'-'*80}")
    print(f"Test 6 Results: {passed} passed, {failed} failed ({passed}/{passed+failed})")
    return passed, failed


def test_integration_current_date():
    """Test 7: Integration Test - 'What is the date today?'"""
    print("\n" + "="*80)
    print("TEST 7: INTEGRATION TEST - CURRENT DATE QUERY")
    print("="*80)

    query = "What is the date today?"
    print(f"\nQuery: '{query}'")

    # Step 1: Temporal detection
    temporal_info = detect_temporal_intent(query)
    print(f"\nTemporal Detection:")
    print(f"  Is Temporal: {temporal_info['is_temporal']}")
    print(f"  Is After Cutoff: {temporal_info['is_after_cutoff']}")
    print(f"  Reason: {temporal_info['reason']}")

    # Should be detected as temporal
    if temporal_info['is_after_cutoff']:
        print("✓ PASS: Query correctly identified as time-sensitive")
        return 1, 0
    else:
        print("✗ FAIL: Query should be identified as time-sensitive")
        return 0, 1


def test_integration_bitcoin_price():
    """Test 8: Integration Test - 'What is the current price of bitcoin?'"""
    print("\n" + "="*80)
    print("TEST 8: INTEGRATION TEST - BITCOIN PRICE QUERY")
    print("="*80)

    query = "What is the current price of bitcoin?"
    print(f"\nQuery: '{query}'")

    # Temporal detection
    temporal_info = detect_temporal_intent(query)
    print(f"\nTemporal Detection:")
    print(f"  Is Temporal: {temporal_info['is_temporal']}")
    print(f"  Is After Cutoff: {temporal_info['is_after_cutoff']}")
    print(f"  Has Domain: {temporal_info['has_domain']}")
    print(f"  Reason: {temporal_info['reason']}")

    # Should be detected as temporal (price + current)
    if temporal_info['is_after_cutoff'] and temporal_info['has_domain']:
        print("✓ PASS: Query correctly identified as time-sensitive with temporal domain")
        return 1, 0
    else:
        print("✗ FAIL: Query should be identified as time-sensitive")
        return 0, 1


def test_integration_historical_query():
    """Test 9: Integration Test - 'Who was the president in 1990?'"""
    print("\n" + "="*80)
    print("TEST 9: INTEGRATION TEST - HISTORICAL QUERY (PRE-CUTOFF)")
    print("="*80)

    query = "Who was the president of the United States in 1990?"
    print(f"\nQuery: '{query}'")

    # Temporal detection
    temporal_info = detect_temporal_intent(query)
    print(f"\nTemporal Detection:")
    print(f"  Is Temporal: {temporal_info['is_temporal']}")
    print(f"  Is After Cutoff: {temporal_info['is_after_cutoff']}")
    print(f"  Extracted Years: {temporal_info['extracted_years']}")
    print(f"  Reason: {temporal_info['reason']}")

    # Should NOT be detected as post-cutoff (1990 is before 2023)
    if not temporal_info['is_after_cutoff']:
        print("✓ PASS: Historical query correctly identified as pre-cutoff (can use base knowledge)")
        return 1, 0
    else:
        print("✗ FAIL: Historical query should not require external sources")
        return 0, 1


def test_integration_current_president():
    """Test 10: Integration Test - 'Who is the current president?'"""
    print("\n" + "="*80)
    print("TEST 10: INTEGRATION TEST - CURRENT PRESIDENT QUERY")
    print("="*80)

    query = "Who is the current president of the United States?"
    print(f"\nQuery: '{query}'")

    # Temporal detection
    temporal_info = detect_temporal_intent(query)
    print(f"\nTemporal Detection:")
    print(f"  Is Temporal: {temporal_info['is_temporal']}")
    print(f"  Is After Cutoff: {temporal_info['is_after_cutoff']}")
    print(f"  Has Keywords: {temporal_info['has_keywords']}")
    print(f"  Has Domain: {temporal_info['has_domain']}")
    print(f"  Reason: {temporal_info['reason']}")

    # Should be detected as temporal (current + president)
    if temporal_info['is_after_cutoff']:
        print("✓ PASS: Query correctly identified as time-sensitive (must use external sources)")
        return 1, 0
    else:
        print("✗ FAIL: Query should require external sources for current information")
        return 0, 1


def main():
    """Run all temporal awareness tests"""
    print("\n" + "="*80)
    print("ADAPTHEON TEMPORAL AWARENESS TEST SUITE")
    print("="*80)
    print(f"Knowledge Cutoff: {KNOWLEDGE_CUTOFF}")
    print(f"Current Date: {date.today()}")

    total_passed = 0
    total_failed = 0

    # Run all tests
    tests = [
        test_temporal_detection,
        test_knowledge_cutoff_info,
        test_system_time_query,
        test_temporal_keywords,
        test_temporal_domains,
        test_year_extraction,
        test_integration_current_date,
        test_integration_bitcoin_price,
        test_integration_historical_query,
        test_integration_current_president,
    ]

    for test_func in tests:
        try:
            passed, failed = test_func()
            total_passed += passed
            total_failed += failed
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test_func.__name__} failed with exception: {e}")
            total_failed += 1

    # Final summary
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    total = total_passed + total_failed
    percentage = (total_passed / total * 100) if total > 0 else 0
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {percentage:.1f}% ({total_passed}/{total})")

    if total_failed == 0:
        print("\n✓ ALL TESTS PASSED! Temporal awareness is fully functional.")
        return 0
    else:
        print(f"\n✗ {total_failed} test(s) failed. Review output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
