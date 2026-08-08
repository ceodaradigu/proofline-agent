"""Compare Proofline's indexed evaluator with its pre-optimization scan."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
from hashlib import sha256
import json
import platform
from statistics import median
from time import perf_counter_ns

from proofline.core import (
    Decision,
    Evidence,
    ProofPacket,
    Requirement,
    _canonical_payload,
    _utc,
    evaluate,
)


BENCHMARK_TIME = datetime(2026, 8, 8, 12, 0, tzinfo=timezone.utc)


def _baseline_evaluate(
    requirements: tuple[Requirement, ...],
    evidence: tuple[Evidence, ...],
    *,
    now: datetime,
) -> ProofPacket:
    """Preserve the original O(requirements × evidence) lookup for comparison."""
    checked_at = _utc(now)
    unmet: list[str] = []
    conflicts: list[str] = []
    for requirement in requirements:
        fresh = []
        for item in evidence:
            if item.requirement_id != requirement.id or not item.authoritative:
                continue
            age_seconds = (checked_at - _utc(item.observed_at)).total_seconds()
            if 0 <= age_seconds <= requirement.max_age_hours * 3600:
                fresh.append(item)
        states = {item.state for item in fresh}
        if len(states) > 1:
            conflicts.append(requirement.id)
        elif states != {"PASS"}:
            unmet.append(requirement.id)

    decision: Decision = (
        "CONFLICT" if conflicts else "NEEDS_EVIDENCE" if unmet else "READY"
    )
    digest = sha256(
        _canonical_payload(requirements, evidence, checked_at, False, False)
    ).hexdigest()
    return ProofPacket(
        decision=decision,
        unmet=tuple(unmet),
        conflicts=tuple(conflicts),
        evidence_count=len(evidence),
        external_action_requested=False,
        human_approved=False,
        packet_hash=digest,
    )


def _fixture(
    requirement_count: int, evidence_per_requirement: int
) -> tuple[tuple[Requirement, ...], tuple[Evidence, ...]]:
    requirements = tuple(
        Requirement(f"req-{index:03d}", f"Requirement {index}")
        for index in range(requirement_count)
    )
    evidence = tuple(
        Evidence(
            requirement.id,
            f"source-{copy}",
            BENCHMARK_TIME,
            "PASS",
            "verified",
        )
        for requirement in requirements
        for copy in range(evidence_per_requirement)
    )
    return requirements, evidence


def benchmark(
    *, iterations: int, repeats: int, requirement_count: int, evidence_per_requirement: int
) -> dict[str, object]:
    if min(iterations, repeats, requirement_count, evidence_per_requirement) <= 0:
        raise ValueError("benchmark dimensions must be positive")
    requirements, evidence = _fixture(requirement_count, evidence_per_requirement)
    baseline_packet = _baseline_evaluate(requirements, evidence, now=BENCHMARK_TIME)
    optimized_packet = evaluate(requirements, evidence, now=BENCHMARK_TIME)
    if baseline_packet != optimized_packet:
        raise RuntimeError("optimized evaluator changed the proof packet")

    samples: list[dict[str, float | int]] = []
    for repeat in range(1, repeats + 1):
        measured: dict[str, float | int] = {"repeat": repeat}
        order = (
            (("baseline", _baseline_evaluate), ("optimized", evaluate))
            if repeat % 2
            else (("optimized", evaluate), ("baseline", _baseline_evaluate))
        )
        for name, evaluator in order:
            gc.collect()
            started = perf_counter_ns()
            for _ in range(iterations):
                packet = evaluator(requirements, evidence, now=BENCHMARK_TIME)
            elapsed_ns = perf_counter_ns() - started
            if packet.packet_hash != baseline_packet.packet_hash:
                raise RuntimeError("packet hash changed during comparison")
            measured[f"{name}_elapsed_ns"] = elapsed_ns
            measured[f"{name}_packets_per_second"] = (
                iterations * 1_000_000_000 / elapsed_ns
            )
        samples.append(measured)

    baseline_rate = median(float(item["baseline_packets_per_second"]) for item in samples)
    optimized_rate = median(float(item["optimized_packets_per_second"]) for item in samples)
    return {
        "schema_version": 1,
        "benchmark": "proofline-indexed-evidence-lookup",
        "architecture": platform.machine(),
        "operating_system": platform.system(),
        "python_version": platform.python_version(),
        "iterations_per_repeat": iterations,
        "repeats": repeats,
        "requirement_count": requirement_count,
        "evidence_count": len(evidence),
        "decision": optimized_packet.decision,
        "packet_hash": optimized_packet.packet_hash,
        "baseline_median_packets_per_second": baseline_rate,
        "optimized_median_packets_per_second": optimized_rate,
        "speedup": optimized_rate / baseline_rate,
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--requirements", type=int, default=256)
    parser.add_argument("--evidence-per-requirement", type=int, default=4)
    parser.add_argument("--output")
    args = parser.parse_args()
    rendered = json.dumps(
        benchmark(
            iterations=args.iterations,
            repeats=args.repeats,
            requirement_count=args.requirements,
            evidence_per_requirement=args.evidence_per_requirement,
        ),
        indent=2,
        sort_keys=True,
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
