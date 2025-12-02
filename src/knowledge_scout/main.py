#!/usr/bin/env python3
"""
Knowledge Scout - Main Entry Point
Supports both interactive and command-line modes
"""

import sys
from .knowledge_processor import KnowledgeProcessor

def main():
    processor = KnowledgeProcessor()
    
    # Command-line argument mode
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        processor.process_query(query)
        return
    
    # Interactive mode
    print("\n" + "="*60)
    print("🧭 KNOWLEDGE SCOUT - Intelligent Information Retrieval")
    print("="*60)
    print("\nType your queries below (or 'exit' to quit)")
    
    # Check API status
    import os
    if os.environ.get('PERPLEXITY_API_KEY'):
        print("✓ Perplexity API enabled")
    else:
        print("ℹ Perplexity API disabled (set PERPLEXITY_API_KEY to enable)")
    
    print("-"*60)
    
    while True:
        try:
            query = input("\n🔍 Query: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
                
            processor.process_query(query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()
