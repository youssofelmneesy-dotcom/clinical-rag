"""
Performance profiling and latency breakdown for the RAG pipeline.
Measures latency at each stage and provides detailed timing reports.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, TypeVar

from backend.config import EVALUATION_DIR

T = TypeVar("T")


@dataclass(frozen=True)
class LatencyBreakdown:
    """Latency breakdown for a single query."""

    question: str
    total_ms: float
    scope_ms: float
    embedding_ms: float
    dense_retrieval_ms: float
    lexical_retrieval_ms: float
    fusion_ms: float
    rerank_ms: float
    generation_ms: float
    citation_validation_ms: float
    claim_verification_ms: float
    overhead_ms: float


@dataclass(frozen=True)
class LatencyStats:
    """Aggregated latency statistics."""

    metric: str
    count: int
    min_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    mean_ms: float


class LatencyProfiler:
    """Measures and tracks latency at each pipeline stage."""

    def __init__(self) -> None:
        self.breakdowns: list[LatencyBreakdown] = []
        self.stage_times: dict[str, list[float]] = {}

    def record_stage(self, stage: str, elapsed_ms: float) -> None:
        """Record timing for a single stage."""
        if stage not in self.stage_times:
            self.stage_times[stage] = []
        self.stage_times[stage].append(elapsed_ms)

    def record_breakdown(self, breakdown: LatencyBreakdown) -> None:
        """Record complete latency breakdown for a query."""
        self.breakdowns.append(breakdown)

    def compute_stats(self) -> dict[str, LatencyStats]:
        """Compute aggregated statistics for each stage."""
        stats = {}
        for stage, times in self.stage_times.items():
            sorted_times = sorted(times)
            stats[stage] = LatencyStats(
                metric=stage,
                count=len(times),
                min_ms=min(times),
                p50_ms=self._percentile(sorted_times, 0.50),
                p90_ms=self._percentile(sorted_times, 0.90),
                p95_ms=self._percentile(sorted_times, 0.95),
                p99_ms=self._percentile(sorted_times, 0.99),
                max_ms=max(times),
                mean_ms=sum(times) / len(times),
            )
        return stats

    def save_report(self, output_path: Path | None = None) -> dict[str, Any]:
        """Save latency report to disk."""
        if output_path is None:
            output_path = EVALUATION_DIR / "final" / "latency_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stats = self.compute_stats()
        report = {
            "breakdowns": [asdict(bd) for bd in self.breakdowns],
            "stats": {name: asdict(stat) for name, stat in stats.items()},
        }

        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

        return report

    def print_summary(self) -> None:
        """Print latency summary to console."""
        stats = self.compute_stats()
        print("\n" + "=" * 80)
        print("LATENCY PROFILE SUMMARY")
        print("=" * 80)
        for stage in sorted(stats.keys()):
            s = stats[stage]
            print(
                f"{stage:30s}: "
                f"P50={s.p50_ms:7.1f}ms P95={s.p95_ms:7.1f}ms P99={s.p99_ms:7.1f}ms "
                f"Mean={s.mean_ms:7.1f}ms Max={s.max_ms:7.1f}ms"
            )

    @staticmethod
    def _percentile(sorted_values: list[float], p: float) -> float:
        """Compute percentile from sorted values."""
        if not sorted_values:
            return 0.0
        idx = int(p * (len(sorted_values) - 1))
        return sorted_values[max(0, min(idx, len(sorted_values) - 1))]


def time_block(name: str, profiler: LatencyProfiler | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to time a function block."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            t0 = time.perf_counter()
            result = func(*args, **kwargs)
            t1 = time.perf_counter()
            elapsed_ms = (t1 - t0) * 1000
            if profiler:
                profiler.record_stage(name, elapsed_ms)
            return result

        return wrapper

    return decorator
