#!/usr/bin/env python3
"""
Adaptheon Internet Services Integration Test
Tests all internet-connected components with real API calls
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=" * 60)
print("  Adaptheon Internet Services Integration Test")
print("=" * 60)
print()

# Test 1: Wikipedia Fetcher
print("[1] Testing Wikipedia Fetcher...")
try:
    from knowledge_scout.fetchers.wikipedia_fetcher import WikipediaFetcher

    wiki = WikipediaFetcher()
    result = wiki.fetch("Python programming")

    if result:
        print(f"✓ Wikipedia fetch successful!")
        print(f"  Query: {result.query}")
        print(f"  Source: {result.source.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Summary: {result.summary[:100]}...")
        print(f"  URL: {result.url}")
    else:
        print("✗ Wikipedia fetch returned None")
        sys.exit(1)
except Exception as e:
    print(f"✗ Wikipedia test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: RSS Fetcher
print("[2] Testing RSS Fetcher...")
try:
    from knowledge_scout.fetchers.rss_fetcher import RSSFetcher

    rss = RSSFetcher()
    result = rss.fetch("technology")

    if result:
        print(f"✓ RSS fetch successful!")
        print(f"  Query: {result.query}")
        print(f"  Source: {result.source.value}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Summary: {result.summary[:150]}...")
    else:
        print("✓ RSS fetch returned None (no matching articles - this is OK)")
except Exception as e:
    print(f"✗ RSS test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Price Service
print("[3] Testing Price Service (CoinGecko API)...")
try:
    from components.price_service import PriceService

    price_svc = PriceService()
    result = price_svc.get_price("bitcoin")

    if result:
        print(f"✓ Price fetch successful!")
        print(f"  Asset: {result['asset']}")
        print(f"  Price: ${result['price_usd']}")
        print(f"  Date: {result['as_of_date']}")
        print(f"  Time: {result['as_of_time']}")
    else:
        print("✗ Price fetch returned None")
        sys.exit(1)
except Exception as e:
    print(f"✗ Price service test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Weather Service
print("[4] Testing Weather Service (Open-Meteo API)...")
try:
    from components.weather_service import WeatherService

    weather_svc = WeatherService()
    result = weather_svc.get_current_weather()

    if result:
        print(f"✓ Weather fetch successful!")
        print(f"  Temperature: {result['temperature_f']:.1f}°F / {result['temperature_c']:.1f}°C")
        print(f"  Wind Speed: {result['windspeed_mph']:.1f} mph")
        print(f"  Date: {result['as_of_date']}")
        print(f"  Time: {result['as_of_time']}")
    else:
        print("✗ Weather fetch returned None")
        sys.exit(1)
except Exception as e:
    print(f"✗ Weather service test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Full Knowledge Scout Integration
print("[5] Testing Full Knowledge Scout Integration...")
try:
    from components.knowledge_scout import KnowledgeScout

    scout = KnowledgeScout()

    # Test search
    result = scout.search("artificial intelligence")

    if result['status'] == 'FOUND':
        print(f"✓ Knowledge Scout search successful!")
        print(f"  Status: {result['status']}")
        print(f"  Source: {result['source']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Summary: {result['summary'][:100]}...")
    else:
        print(f"✗ Knowledge Scout search failed: {result['status']}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Knowledge Scout test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 6: Semantic Utils (Regex Fix Validation)
print("[6] Testing Semantic Utils (Regex Fix Validation)...")
try:
    from components.semantic_utils import tokenize, text_to_vector, cosine_similarity

    # Test tokenization
    text = "Hello World 123 Test"
    tokens = tokenize(text)

    if tokens == ['hello', 'world', '123', 'test']:
        print(f"✓ Tokenization works correctly!")
        print(f"  Input: '{text}'")
        print(f"  Tokens: {tokens}")
    else:
        print(f"✗ Tokenization failed: {tokens}")
        sys.exit(1)

    # Test vector creation
    vec = text_to_vector("machine learning")
    if 'machine' in vec and 'learning' in vec:
        print(f"✓ Vector creation works correctly!")
    else:
        print(f"✗ Vector creation failed: {vec}")
        sys.exit(1)

    # Test cosine similarity
    vec1 = text_to_vector("artificial intelligence")
    vec2 = text_to_vector("machine learning AI")
    sim = cosine_similarity(vec1, vec2)

    if 0 <= sim <= 1:
        print(f"✓ Cosine similarity works correctly!")
        print(f"  Similarity: {sim:.4f}")
    else:
        print(f"✗ Cosine similarity failed: {sim}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Semantic utils test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("  ✓ ALL INTERNET SERVICES TESTS PASSED!")
print("=" * 60)
print()
print("Summary:")
print("  ✓ Wikipedia Fetcher - Working")
print("  ✓ RSS Fetcher - Working")
print("  ✓ Price Service (CoinGecko) - Working")
print("  ✓ Weather Service (Open-Meteo) - Working")
print("  ✓ Knowledge Scout Integration - Working")
print("  ✓ Semantic Utils (Regex Fixes) - Working")
print()
print("All internet-connected components are functioning correctly!")
