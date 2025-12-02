import time
from knowledge_scout.fetchers.fetcher_chain import FetcherChain
from knowledge_scout.verifiers.composite_verifier import CompositeVerifier

class KnowledgeScout:
    """
    Phase 2: Full fetch + verify + store pipeline
    """
    def __init__(self, memory, confidence_threshold=0.65):
        self.fetcher = FetcherChain()
        self.verifier = CompositeVerifier(memory)
        self.memory = memory
        self.threshold = confidence_threshold

    def scout(self, question, category='general'):
        print("  [Knowledge Scout] Launching for: '{}'".format(question))
        start_time = time.time()

        # Step 1: Fetch
        fetch_result = self.fetcher.fetch(question)

        # Step 2: Verify
        verification = self.verifier.verify(
            answer=fetch_result.answer,
            citations=fetch_result.citations,
            context=question
        )

        print("  [Verification] Confidence: {:.2f} | Passed: {}".format(
            verification.confidence, verification.passed
        ))

        # Step 3: Decide whether to store
        should_store = (
            verification.passed and
            not verification.needs_review and
            verification.confidence > self.threshold
        )

        if should_store:
            # Store in semantic memory
            knowledge_key = "knowledge_" + question.lower().replace(" ", "_")[:50]
            self.memory.layers["semantic"][knowledge_key] = {
                "content": fetch_result.answer,
                "confidence": verification.confidence,
                "sources": [c.url for c in fetch_result.citations],
                "timestamp": time.time(),
                "category": category
            }
            self.memory.save_memory()
            print("  [Scout] Stored new knowledge under key '{}'".format(knowledge_key))
        else:
            print("  [Scout] Confidence too low, not storing")

        total_time = int((time.time() - start_time) * 1000)

        return {
            "question": question,
            "answer": fetch_result.answer,
            "source": fetch_result.source.value,
            "confidence": verification.confidence,
            "stored": should_store,
            "needs_review": verification.needs_review,
            "time_ms": total_time,
            "citations": [
                {"title": c.title, "url": c.url}
                for c in fetch_result.citations
            ],
        }
