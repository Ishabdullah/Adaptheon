import textwrap
from .fetchers.fetcher_chain import FetcherChain
from .verifiers.simple_verifier import SimpleVerifier

class KnowledgeProcessor:
    def __init__(self):
        self.fetcher_chain = FetcherChain()
        self.verifier = SimpleVerifier()

    def process_query(self, query: str):
        """
        Fetches, verifies, and formats the response for a given query.
        """
        # Fetch information
        fetch_result = self.fetcher_chain.fetch(query)
        
        # Verify quality
        verification_result = self.verifier.verify(fetch_result)
        
        # Display results
        self._print_formatted_output(query, fetch_result, verification_result)

    def _print_formatted_output(self, query, fetch_result, verification_result):
        """Prints a user-friendly summary of the results."""
        
        print("\n" + "="*50)
        print(f"🔎 KNOWLEDGE SCOUT REPORT: '{query}'")
        print("="*50)

        # Status and confidence
        confidence_bar = self._get_confidence_bar(verification_result.confidence)
        status = "✅ VERIFIED" if verification_result.is_verified else "⚠️  UNVERIFIED"
        print(f"Status: {status} | Confidence: {confidence_bar} ({verification_result.confidence * 100:.0f}%)")
        print(f"Reason: {verification_result.reason}")
        print(f"Source: {fetch_result.source.value} | Fetch Time: {fetch_result.fetch_time}ms")
        print("-"*50)

        # Answer
        print("📝 ANSWER:")
        wrapped_answer = textwrap.fill(fetch_result.answer, width=70, 
                                      initial_indent="  ", subsequent_indent="  ")
        print(wrapped_answer)
        
        # Citations
        if fetch_result.citations:
            print("\n📚 CITATIONS:")
            for i, citation in enumerate(fetch_result.citations, 1):
                print(f"  [{i}] {citation.title}")
                print(f"      {citation.url}")
        else:
            print("\n📚 CITATIONS: None provided.")
            
        print("="*50 + "\n")

    def _get_confidence_bar(self, confidence_value):
        """Generates a visual confidence indicator."""
        bar_length = 20
        filled_length = int(bar_length * confidence_value)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        return f"[{bar}]"
