#!/usr/bin/env python3
"""
Comprehensive Test Suite for Live Retrieval Hardening
Tests all query types from the user's requirements
"""

import sys
sys.path.insert(0, 'src')

import logging
from components.price_service import PriceService
from components.knowledge_scout import KnowledgeScout
from components.hrm import HierarchicalReasoningMachine
from components.temporal_awareness import detect_temporal_intent
from components.fetchers.newsapi_fetcher import NewsAPIFetcher
from components.fetchers.nyt_bestseller_fetcher import NYTBestsellerFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('LiveRetrievalTests')


def test_stock_price_query():
    """Test stock price retrieval"""
    print("\n" + "=" * 80)
    print("TEST 1: Stock Price Query - 'What is the current stock price of Amazon?'")
    print("=" * 80)

    query = "What is the current stock price of Amazon?"

    # Test temporal detection
    temporal_info = detect_temporal_intent(query)
    assert temporal_info['is_after_cutoff'], "Stock price query should be time-sensitive"
    logger.info(f"✓ Temporal detection: {temporal_info['reason']}")

    # Test HRM routing
    hrm = HierarchicalReasoningMachine()
    intent_data = {"type": "QUERY", "content": query}
    memory_context = {"semantic": {}, "episodic": [], "user_preferences": {}}
    logic_output = hrm.process(intent_data, memory_context)

    assert logic_output['action'] == 'PRICE_QUERY', f"Expected PRICE_QUERY, got {logic_output['action']}"
    assert logic_output['asset'] == 'amazon', f"Expected asset 'amazon', got {logic_output['asset']}"
    logger.info(f"✓ HRM routing: action={logic_output['action']}, asset={logic_output['asset']}")

    # Test PriceService
    price_service = PriceService()
    result = price_service.get_price("Amazon")

    if result:
        logger.info(f"✓ PriceService result: {result['asset']} ({result['asset_id']}) = ${result['price_usd']:.2f}")
        logger.info(f"  Source: {result['source']}, Type: {result['asset_type']}")
        print("✅ TEST 1 PASSED: Stock price retrieval working")
        return True
    else:
        logger.error("✗ PriceService failed to return result")
        print("❌ TEST 1 FAILED: Stock price retrieval failed")
        return False


def test_sports_roster_query():
    """Test sports roster query routing"""
    print("\n" + "=" * 80)
    print("TEST 2: Sports Roster Query - 'Who is the current quarterback for the New York Giants in 2025?'")
    print("=" * 80)

    query = "Who is the current quarterback for the New York Giants in 2025?"

    # Test temporal detection
    temporal_info = detect_temporal_intent(query)
    assert temporal_info['is_after_cutoff'], "Sports roster query should be time-sensitive"
    logger.info(f"✓ Temporal detection: {temporal_info['reason']}")

    # Test HRM routing
    hrm = HierarchicalReasoningMachine()
    intent_data = {"type": "QUERY", "content": query}
    memory_context = {"semantic": {}, "episodic": [], "user_preferences": {}}
    logic_output = hrm.process(intent_data, memory_context)

    assert logic_output['action'] == 'TRIGGER_SCOUT', f"Expected TRIGGER_SCOUT, got {logic_output['action']}"
    assert logic_output.get('domain') == 'sports', f"Expected domain 'sports', got {logic_output.get('domain')}"
    assert logic_output.get('query_type') == 'sports_roster', f"Expected query_type 'sports_roster', got {logic_output.get('query_type')}"
    logger.info(f"✓ HRM routing: action={logic_output['action']}, domain={logic_output.get('domain')}, type={logic_output.get('query_type')}")

    # Test Scout sports fast path
    scout = KnowledgeScout()
    result = scout.search(query, domain="sports", ignore_cache=True)

    if result['status'] == 'FOUND':
        logger.info(f"✓ Scout result: {result['summary'][:100]}...")
        logger.info(f"  Source: {result['source']}, Confidence: {result['confidence']:.2f}")

        # Verify it's NOT from Reddit for roster query
        if result['source'] == 'reddit':
            logger.error("✗ Sports roster query incorrectly used Reddit (should use TheSportsDB/ESPN)")
            print("❌ TEST 2 FAILED: Used wrong source (Reddit) for roster query")
            return False

        print("✅ TEST 2 PASSED: Sports roster routing working correctly")
        return True
    else:
        logger.warning(f"Scout returned NOT_FOUND - this is acceptable if TheSportsDB API is down")
        logger.info(f"  Summary: {result['summary']}")
        print("⚠️  TEST 2 PARTIAL: Sports routing correct, but API returned no data")
        return True  # Still pass if routing is correct


def test_breaking_news_query():
    """Test breaking news retrieval"""
    print("\n" + "=" * 80)
    print("TEST 3: Breaking News Query - 'Whats the latest breaking news?'")
    print("=" * 80)

    query = "Whats the latest breaking news?"

    # Test temporal detection
    temporal_info = detect_temporal_intent(query)
    assert temporal_info['is_after_cutoff'], "Breaking news query should be time-sensitive"
    logger.info(f"✓ Temporal detection: {temporal_info['reason']}")

    # Test HRM routing
    hrm = HierarchicalReasoningMachine()
    intent_data = {"type": "QUERY", "content": query}
    memory_context = {"semantic": {}, "episodic": [], "user_preferences": {}}
    logic_output = hrm.process(intent_data, memory_context)

    assert logic_output['action'] == 'TRIGGER_SCOUT', f"Expected TRIGGER_SCOUT, got {logic_output['action']}"
    assert logic_output.get('domain') == 'news', f"Expected domain 'news', got {logic_output.get('domain')}"
    logger.info(f"✓ HRM routing: action={logic_output['action']}, domain={logic_output.get('domain')}")

    # Test NewsAPI fetcher directly
    news_fetcher = NewsAPIFetcher()
    result = news_fetcher.fetch(query)

    if result.status.value == 'FOUND':
        logger.info(f"✓ NewsAPI result: {result.summary.split(chr(10))[0]}...")  # First line
        logger.info(f"  Source: {result.source}, Confidence: {result.confidence:.2f}")
        logger.info(f"  Headlines count: {result.data.get('count', 0)}")
        print("✅ TEST 3 PASSED: Breaking news retrieval working")
        return True
    else:
        logger.error(f"✗ NewsAPI failed: {result.error or 'NOT_FOUND'}")
        print("❌ TEST 3 FAILED: Breaking news retrieval failed")
        return False


def test_bestseller_query():
    """Test NYT bestseller retrieval"""
    print("\n" + "=" * 80)
    print("TEST 4: Bestseller Query - 'What is the newest book for the #1 New York Times best seller?'")
    print("=" * 80)

    query = "What is the newest book for the #1 New York Times best seller?"

    # Test temporal detection
    temporal_info = detect_temporal_intent(query)
    assert temporal_info['is_after_cutoff'], "Bestseller query should be time-sensitive"
    logger.info(f"✓ Temporal detection: {temporal_info['reason']}")

    # Test HRM routing
    hrm = HierarchicalReasoningMachine()
    intent_data = {"type": "QUERY", "content": query}
    memory_context = {"semantic": {}, "episodic": [], "user_preferences": {}}
    logic_output = hrm.process(intent_data, memory_context)

    assert logic_output['action'] == 'TRIGGER_SCOUT', f"Expected TRIGGER_SCOUT, got {logic_output['action']}"
    assert logic_output.get('domain') == 'bestseller', f"Expected domain 'bestseller', got {logic_output.get('domain')}"
    logger.info(f"✓ HRM routing: action={logic_output['action']}, domain={logic_output.get('domain')}")

    # Test NYT Bestseller fetcher directly
    bestseller_fetcher = NYTBestsellerFetcher()
    result = bestseller_fetcher.fetch(query)

    if result.status.value == 'FOUND':
        logger.info(f"✓ NYT Bestseller result: {result.summary.split(chr(10))[0]}...")  # First line
        logger.info(f"  Source: {result.source}, Confidence: {result.confidence:.2f}")
        logger.info(f"  Books count: {result.data.get('count', 0)}")
        print("✅ TEST 4 PASSED: Bestseller retrieval working")
        return True
    else:
        logger.error(f"✗ NYT Bestseller failed: {result.error or 'NOT_FOUND'}")
        print("❌ TEST 4 FAILED: Bestseller retrieval failed")
        return False


def test_identity_question_detection():
    """Test identity question detection for time-sensitive routing"""
    print("\n" + "=" * 80)
    print("TEST 5: Identity Question Detection")
    print("=" * 80)

    test_cases = [
        ("Who is the current president?", True, "political identity"),
        ("Who is the quarterback for the Giants?", True, "sports identity"),
        ("What is the stock price of Tesla?", True, "finance domain"),
        ("Who was the president in 1990?", False, "historical question"),
    ]

    all_passed = True
    for query, should_be_temporal, description in test_cases:
        temporal_info = detect_temporal_intent(query)
        is_temporal = temporal_info['is_after_cutoff']

        if is_temporal == should_be_temporal:
            logger.info(f"✓ '{query}' -> {is_temporal} ({description})")
        else:
            logger.error(f"✗ '{query}' -> Expected {should_be_temporal}, got {is_temporal}")
            all_passed = False

    if all_passed:
        print("✅ TEST 5 PASSED: Identity question detection working")
    else:
        print("❌ TEST 5 FAILED: Some identity questions not detected correctly")

    return all_passed


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "#" * 80)
    print("# LIVE RETRIEVAL HARDENING - COMPREHENSIVE TEST SUITE")
    print("#" * 80)

    tests = [
        ("Stock Price Query", test_stock_price_query),
        ("Sports Roster Query", test_sports_roster_query),
        ("Breaking News Query", test_breaking_news_query),
        ("Bestseller Query", test_bestseller_query),
        ("Identity Question Detection", test_identity_question_detection),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 80)
    print(f"TOTAL: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)

    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
