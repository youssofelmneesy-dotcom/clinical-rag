from __future__ import annotations

import argparse

from backend.pipeline import ClinicalRagPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the COPD clinical RAG system a question.")
    parser.add_argument("question", help="COPD clinical question")
    parser.add_argument("--k", type=int, default=5, help="Number of evidence chunks to retrieve")
    args = parser.parse_args()

    response = ClinicalRagPipeline().answer(args.question, k=args.k)
    print(response.final_text)
    print()
    print(f"Confidence: {response.confidence.confidence:.3f} (threshold {response.confidence.threshold:.3f})")
    print(f"Scope: {response.scope.reason}")
    print(f"Claim verification: {response.verification.reason}")


if __name__ == "__main__":
    main()
