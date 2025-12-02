#!/usr/bin/env python3
"""Test suite for Knowledge Scout"""

from .knowledge_processor import KnowledgeProcessor

def run_tests():
    tests = [
        "What are the latest developments in AI?",
        "What is quantum computing?",
        "Latest climate change news"
    ]
    
    print("\n" + "="*60)
    print("🧪 KNOWLEDGE SCOUT TEST SUITE")
    print("="*60)
    print(f"\nRunning {len(tests)} test queries...\n")
    
    processor = KnowledgeProcessor()
    
    for i, query in enumerate(tests, 1):
        print(f"\n{'─'*60}")
        print(f"TEST {i}/{len(tests)}: {query}")
        print(f"{'─'*60}")
        processor.process_query(query)
        
        if i < len(tests):
            input("\n⏸️  Press Enter for next test...")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_tests()
