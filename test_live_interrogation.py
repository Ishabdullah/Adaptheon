#!/usr/bin/env python3
"""
Comprehensive Live Interrogation of Adaptheon
Tests all identity, architecture, and domain-specific capabilities
"""

import sys
import os
sys.path.append(os.path.join(os.getcwd(), "src"))

from meta_core import MetaCognitiveCore

def test_identity_and_architecture():
    """Test identity and architecture awareness"""
    print("\n" + "="*80)
    print("PHASE 1: IDENTITY & ARCHITECTURE INTERROGATION")
    print("="*80)

    core = MetaCognitiveCore()

    questions = [
        "Who are you?",
        "What can you do?",
        "How do you work?",
        "What's your architecture?",
        "Describe your design.",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n[Q{i}] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"[A{i}] {response}")

        # Validate response mentions Adaptheon
        if "adaptheon" in response.lower():
            print("✓ Mentions 'Adaptheon'")
        else:
            print("⚠ Does NOT mention 'Adaptheon'")

def test_knowledge_services():
    """Test Wikidata/Wikipedia knowledge retrieval"""
    print("\n" + "="*80)
    print("PHASE 2: KNOWLEDGE & REFERENCE SERVICES")
    print("="*80)

    core = MetaCognitiveCore()

    tests = [
        ("Wikidata", "Who is the current president of the United States?"),
        ("Wikipedia", "What is Bitcoin?"),
        ("Wikidata", "What is the population of Tokyo?"),
    ]

    for service, question in tests:
        print(f"\n[{service}] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"Response: {response}")

def test_weather_services():
    """Test weather services"""
    print("\n" + "="*80)
    print("PHASE 3: WEATHER & LOCATION SERVICES")
    print("="*80)

    core = MetaCognitiveCore()

    tests = [
        "What's the current weather in New York City?",
        "What is the temperature in London?",
    ]

    for question in tests:
        print(f"\n[Weather] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"Response: {response}")
        if "°F" in response or "degrees" in response.lower():
            print("✓ Contains temperature data")

def test_finance_services():
    """Test finance and crypto services"""
    print("\n" + "="*80)
    print("PHASE 4: FINANCE & CRYPTOCURRENCY SERVICES")
    print("="*80)

    core = MetaCognitiveCore()

    tests = [
        "What is the current price of bitcoin?",
        "What is the current price of Apple stock?",
    ]

    for question in tests:
        print(f"\n[Finance] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"Response: {response}")
        if "$" in response or "dollar" in response.lower():
            print("✓ Contains price data")

def test_academic_services():
    """Test academic paper services"""
    print("\n" + "="*80)
    print("PHASE 5: ACADEMIC & RESEARCH SERVICES")
    print("="*80)

    core = MetaCognitiveCore()

    tests = [
        "Find me a recent paper about machine learning",
        "What is quantum computing?",
    ]

    for question in tests:
        print(f"\n[Academic] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"Response: {response}")

def test_media_services():
    """Test media and entertainment services"""
    print("\n" + "="*80)
    print("PHASE 6: MEDIA & ENTERTAINMENT SERVICES")
    print("="*80)

    core = MetaCognitiveCore()

    tests = [
        "Tell me about the book '1984'",
        "Who is the artist behind the song 'Bohemian Rhapsody'?",
    ]

    for question in tests:
        print(f"\n[Media] {question}")
        print("-" * 80)
        response = core.run_cycle(question)
        print(f"Response: {response}")

def test_memory_systems():
    """Test memory persistence"""
    print("\n" + "="*80)
    print("PHASE 7: MEMORY SYSTEMS")
    print("="*80)

    core = MetaCognitiveCore()

    print("\n[Memory Write]")
    print("-" * 80)
    response1 = core.run_cycle("Remember that my favorite color is blue")
    print(f"Response: {response1}")

    print("\n[Memory Read]")
    print("-" * 80)
    response2 = core.run_cycle("What do you know about me?")
    print(f"Response: {response2}")
    if "blue" in response2.lower():
        print("✓ Memory persisted correctly")

def main():
    """Run comprehensive interrogation"""
    print("="*80)
    print("ADAPTHEON COMPREHENSIVE LIVE INTERROGATION")
    print("Testing all systems through real production interface")
    print("="*80)

    try:
        test_identity_and_architecture()
        test_knowledge_services()
        test_weather_services()
        test_finance_services()
        test_academic_services()
        test_media_services()
        test_memory_systems()

        print("\n" + "="*80)
        print("INTERROGATION COMPLETE")
        print("All phases executed successfully")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] Interrogation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
