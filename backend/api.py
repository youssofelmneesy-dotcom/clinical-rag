"""
Production-grade API server for the Clinical RAG system.
Provides REST endpoints for querying and health checks.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
except ImportError:
    FastAPI = None  # type: ignore
    HTTPException = None  # type: ignore
    Query = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    JSONResponse = None  # type: ignore
    BaseModel = None  # type: ignore
    Field = None  # type: ignore

from backend.models import EvidenceResult
from backend.pipeline import ClinicalRagPipeline


@dataclass(frozen=True)
class CitationDetail:
    """Citation with full details."""

    chunk_id: str
    document: str
    source_filename: str
    section: str
    page: int


@dataclass(frozen=True)
class EvidenceDetail:
    """Retrieved evidence item."""

    rank: int
    chunk_id: str
    document: str
    section: str
    page: int
    similarity: float
    preview: str


@dataclass(frozen=True)
class QueryMetrics:
    """Query performance metrics."""

    latency_ms: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    validation_latency_ms: float


@dataclass(frozen=True)
class HealthResponse:
    """Health check response."""

    status: str
    service: str
    version: str
    timestamp: str


@dataclass(frozen=True)
class QueryResponse:
    """Standard API response for a query."""

    answer: str | None
    status: str
    confidence: float | None
    confidence_threshold: float | None
    citations: list[CitationDetail]
    evidence: list[EvidenceDetail]
    in_scope: bool
    claims_verified: bool
    metrics: QueryMetrics | None = None
    reason: str | None = None


class QueryRequest(BaseModel):
    """Query request model."""

    question: str
    k: int = Field(default=5, ge=1, le=20)
    show_evidence: bool = False


def create_app() -> FastAPI | None:
    """Create and configure the FastAPI application."""
    if FastAPI is None:
        return None

    app = FastAPI(
        title="Clinical RAG API",
        description="Evidence-grounded COPD clinical guidance",
        version="1.0.0",
    )

    # Add CORS middleware
    allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    pipeline = ClinicalRagPipeline()

    @app.get("/health", response_model=dict)
    async def health():
        """Health check endpoint."""
        from datetime import datetime

        response = HealthResponse(
            status="ok",
            service="clinical-rag",
            version="1.0.0",
            timestamp=datetime.utcnow().isoformat(),
        )
        return asdict(response)

    @app.post("/query", response_model=dict)
    async def query(request: QueryRequest):
        """Process a clinical question and return grounded answer."""
        t0 = time.perf_counter()

        try:
            response = pipeline.answer(request.question, k=request.k)
            t1 = time.perf_counter()

            # Build citations
            citations = [
                CitationDetail(
                    chunk_id=source.get("chunk_id", ""),
                    document=source.get("document", ""),
                    source_filename=source.get("source_filename", ""),
                    section=source.get("section", ""),
                    page=source.get("page", 0),
                )
                for source in response.answer.sources
            ]

            # Build evidence
            evidence = [
                EvidenceDetail(
                    rank=rank,
                    chunk_id=item.chunk_id,
                    document=item.document,
                    section=item.section,
                    page=item.page,
                    similarity=item.similarity,
                    preview=item.text[:200].replace("\n", " "),
                )
                for rank, item in enumerate(response.evidence[:request.k], start=1)
            ]

            # Build metrics
            total_latency_ms = (time.perf_counter() - t0) * 1000
            metrics = QueryMetrics(
                latency_ms=total_latency_ms,
                retrieval_latency_ms=0.0,  # TODO: instrument pipeline
                generation_latency_ms=0.0,  # TODO: instrument pipeline
                validation_latency_ms=0.0,  # TODO: instrument pipeline
            )

            # Determine status
            if not response.scope.in_scope:
                status = "out_of_scope"
                answer = None
            elif not response.confidence.sufficient:
                status = "insufficient_evidence"
                answer = None
            elif not response.verification.supported:
                status = "claim_verification_failed"
                answer = None
            else:
                status = "answered"
                answer = response.final_text

            api_response = QueryResponse(
                answer=answer,
                status=status,
                confidence=response.confidence.confidence if response.confidence.sufficient else None,
                confidence_threshold=response.confidence.threshold,
                citations=citations,
                evidence=evidence if request.show_evidence else [],
                in_scope=response.scope.in_scope,
                claims_verified=response.verification.supported,
                metrics=metrics,
                reason=response.scope.reason if not response.scope.in_scope else None,
            )

            return asdict(api_response)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


if __name__ == "__main__":
    if FastAPI is None:
        print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    else:
        import uvicorn

        app = create_app()
        uvicorn.run(
            app,
            host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", "8000")),
            workers=1,
        )
