#!/usr/bin/env python
"""
End-to-End Integration Tests
Tests real queries against the live backend API
"""
import json
import time
import requests
from typing import Any

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            assert data["status"] == "ok"
            assert data["service"] == "clinical-rag"
            print("✓ Health check passed")
            self.results.append(("health", True, None))
            return True
        except Exception as e:
            print(f"✗ Health check failed: {e}")
            self.results.append(("health", False, str(e)))
            return False
    
    def query(self, question: str, k: int = 5) -> dict[str, Any] | None:
        """Submit a clinical query"""
        try:
            resp = requests.post(
                f"{self.base_url}/query",
                json={"question": question, "k": k, "show_evidence": True},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"✗ Query failed: {e}")
            return None
    
    def test_answerable_question(self) -> bool:
        """Test an answerable COPD question"""
        question = "What are the diagnostic criteria for COPD according to GOLD?"
        print(f"\n[TEST] Answerable question: {question}")
        
        response = self.query(question)
        if not response:
            self.results.append(("answerable_question", False, "No response"))
            return False
        
        try:
            assert response["status"] == "answered", f"Status was {response['status']}"
            assert response["answer"] is not None, "Answer is None"
            assert len(response["answer"]) > 0, "Answer is empty"
            assert response["in_scope"] is True, "Question marked as out of scope"
            assert response["claims_verified"] is True, "Claims not verified"
            assert len(response["citations"]) > 0, "No citations"
            assert len(response["evidence"]) > 0, "No evidence"
            
            print(f"  Status: {response['status']}")
            print(f"  Answer length: {len(response['answer'])} chars")
            print(f"  Citations: {len(response['citations'])}")
            print(f"  Evidence chunks: {len(response['evidence'])}")
            print(f"  Confidence: {response['confidence']:.3f}")
            print(f"  Latency: {response['metrics']['latency_ms']:.1f}ms")
            
            self.results.append(("answerable_question", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("answerable_question", False, str(e)))
            return False
    
    def test_multiple_answers(self) -> bool:
        """Test another answerable question"""
        question = "What inhaled therapies are recommended for COPD?"
        print(f"\n[TEST] Multiple evidence question: {question}")
        
        response = self.query(question)
        if not response:
            self.results.append(("multiple_answers", False, "No response"))
            return False
        
        try:
            assert response["status"] == "answered"
            assert response["answer"] is not None
            assert len(response["citations"]) > 0
            
            print(f"  Status: {response['status']}")
            print(f"  Citations: {len(response['citations'])}")
            print(f"  First citation: {response['citations'][0]['document']}")
            
            self.results.append(("multiple_answers", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("multiple_answers", False, str(e)))
            return False
    
    def test_out_of_scope(self) -> bool:
        """Test out-of-scope question"""
        question = "What are the best restaurants in Paris?"
        print(f"\n[TEST] Out-of-scope question: {question}")
        
        response = self.query(question)
        if not response:
            self.results.append(("out_of_scope", False, "No response"))
            return False
        
        try:
            # Should be out of scope or insufficient evidence
            assert response["status"] in ("out_of_scope", "insufficient_evidence"), \
                f"Status was {response['status']}, expected out_of_scope or insufficient_evidence"
            assert response["answer"] is None, "Answer should be None for out of scope"
            assert response["in_scope"] is False or not response["claims_verified"]
            
            print(f"  Status: {response['status']}")
            print(f"  Reason: {response['reason']}")
            
            self.results.append(("out_of_scope", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("out_of_scope", False, str(e)))
            return False
    
    def test_insufficient_evidence(self) -> bool:
        """Test question with insufficient evidence"""
        question = "What is the prognosis for a specific patient with COPD given their medical history?"
        print(f"\n[TEST] Individualized/insufficient evidence question: {question}")
        
        response = self.query(question)
        if not response:
            self.results.append(("insufficient_evidence", False, "No response"))
            return False
        
        try:
            # Should decline due to insufficient evidence or patient-specific nature
            assert response["status"] in ("insufficient_evidence", "out_of_scope"), \
                f"Status was {response['status']}"
            assert response["answer"] is None, "Answer should be None"
            
            print(f"  Status: {response['status']}")
            print(f"  In scope: {response['in_scope']}")
            print(f"  Claims verified: {response['claims_verified']}")
            
            self.results.append(("insufficient_evidence", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("insufficient_evidence", False, str(e)))
            return False
    
    def test_citation_structure(self) -> bool:
        """Test that citations have all required fields"""
        question = "What does GOLD recommend for COPD diagnosis?"
        print(f"\n[TEST] Citation structure: {question}")
        
        response = self.query(question)
        if not response or response["status"] != "answered":
            self.results.append(("citation_structure", False, "No answered response"))
            return False
        
        try:
            for citation in response["citations"]:
                assert "chunk_id" in citation, "Missing chunk_id"
                assert "document" in citation, "Missing document"
                assert "source_filename" in citation, "Missing source_filename"
                assert "section" in citation, "Missing section"
                assert "page" in citation, "Missing page"
            
            print(f"  Total citations: {len(response['citations'])}")
            for i, cit in enumerate(response['citations'][:2], 1):
                print(f"  Citation {i}: {cit['document']} | Page {cit['page']} | {cit['section']}")
            
            self.results.append(("citation_structure", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("citation_structure", False, str(e)))
            return False
    
    def test_evidence_structure(self) -> bool:
        """Test that evidence has all required fields"""
        question = "What is spirometry in COPD?"
        print(f"\n[TEST] Evidence structure: {question}")
        
        response = self.query(question)
        if not response or response["status"] != "answered":
            self.results.append(("evidence_structure", False, "No answered response"))
            return False
        
        try:
            for evidence in response["evidence"]:
                assert "rank" in evidence, "Missing rank"
                assert "chunk_id" in evidence, "Missing chunk_id"
                assert "document" in evidence, "Missing document"
                assert "section" in evidence, "Missing section"
                assert "page" in evidence, "Missing page"
                assert "similarity" in evidence, "Missing similarity"
                assert "preview" in evidence, "Missing preview"
            
            print(f"  Total evidence chunks: {len(response['evidence'])}")
            for i, ev in enumerate(response['evidence'][:2], 1):
                print(f"  Chunk {i}: Rank {ev['rank']} | Similarity {ev['similarity']:.3f} | {ev['document']}")
            
            self.results.append(("evidence_structure", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("evidence_structure", False, str(e)))
            return False
    
    def test_performance(self) -> bool:
        """Test that response times are within expected range"""
        question = "What are risk factors for COPD?"
        print(f"\n[TEST] Performance: {question}")
        
        start = time.time()
        response = self.query(question)
        total_time = (time.time() - start) * 1000
        
        if not response or response["status"] != "answered":
            self.results.append(("performance", False, "No answered response"))
            return False
        
        try:
            api_latency = response["metrics"]["latency_ms"]
            # Warm response should be < 2 seconds
            assert api_latency < 2000, f"API latency {api_latency}ms exceeds 2000ms"
            assert total_time < 2500, f"Total time {total_time}ms exceeds 2500ms"
            
            print(f"  API latency: {api_latency:.1f}ms")
            print(f"  Total round-trip: {total_time:.1f}ms")
            print(f"  P50 expected: 348ms, P95 expected: 843ms")
            
            self.results.append(("performance", True, None))
            return True
        except AssertionError as e:
            print(f"  ✗ Assertion failed: {e}")
            self.results.append(("performance", False, str(e)))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)
        
        for test_name, result, error in self.results:
            status = "✓ PASS" if result else "✗ FAIL"
            error_msg = f" ({error})" if error else ""
            print(f"{status:8} {test_name:25} {error_msg}")
        
        print("=" * 70)
        print(f"Result: {passed}/{total} tests passed")
        print("=" * 70)
        
        return passed == total

if __name__ == "__main__":
    print("Clinical RAG - End-to-End Integration Tests")
    print("=" * 70)
    
    tester = APITester()
    
    # Run all tests
    tester.test_health()
    tester.test_answerable_question()
    tester.test_multiple_answers()
    tester.test_out_of_scope()
    tester.test_insufficient_evidence()
    tester.test_citation_structure()
    tester.test_evidence_structure()
    tester.test_performance()
    
    # Print summary
    success = tester.print_summary()
    exit(0 if success else 1)
