from __future__ import annotations

import argparse

from backend.pipeline import ClinicalRagPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the COPD clinical RAG system a question.")
    parser.add_argument("question", help="COPD clinical question")
    parser.add_argument("--k", type=int, default=5, help="Number of evidence chunks to retrieve")
    parser.add_argument("--show-evidence", action="store_true", help="Print retrieved evidence before the final answer")
    args = parser.parse_args()

    response = ClinicalRagPipeline().answer(args.question, k=args.k)
    if args.show_evidence:
        print("Retrieved Evidence:")
        for rank, item in enumerate(response.evidence, start=1):
            print(
                f"{rank}. score={item.similarity:.3f} document={item.document} "
                f"section={item.section} page={item.page} chunk={item.chunk_id}"
            )
            print(item.text[:500].replace("\n", " "))
            print()
        print("Final Answer:")
    print(response.final_text)
    print()
    print(f"Confidence: {response.confidence.confidence:.3f} (threshold {response.confidence.threshold:.3f})")
    print(f"Scope: {response.scope.reason}")
    print(f"Claim verification: {response.verification.reason}")


if __name__ == "__main__":
    main()
