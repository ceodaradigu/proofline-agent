"""Benchmark Proofline's deterministic gate without network or cloud credentials."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import gc
import json
import platform
from statistics import median
from time import perf_counter_ns

from proofline import Evidence, Requirement, evaluate


BENCHMARK_TIME = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)
REQUIREMENTS = (
    Requirement("source-open", "Authoritative source confirms the task is open"),
    Requirement("payment-funded", "Reward is funded and collectible"),
    Requirement("deliverable-tested", "Deliverable passes its acceptance test"),
)
EVIDENCE = (
    Evidence("source-open", "official-source", BENCHMARK_TIME, "PASS", "open"),
    Evidence("payment-funded", "payment-ledger", BENCHMARK_TIME, "PASS", "funded"),
    Evidence(
        "deliverable-tested",
        "ci-run",
        BENCHMARK_TIME - timedelta(minutes=2),
        "PASS",
        "tests passed",
    ),
)


def _evaluate_once():
    return evaluate(
        REQUIREMENTS,
        EVIDENCE,
        now=BENCHMARK_TIME,
        external_action_requested=True,
        human_approved=True,
    )


def benchmark(*, iterations: int, repeats: int) -> dict[str, object]:
    """Return machine-readable timing samples for the deterministic core."""

    if iterations <= 0:
        raise ValueError("iterations must be positive")
    if repeats <= 0:
        raise ValueError("repeats must be positive")

    expected = _evaluate_once()
    if expected.decision != "READY":
        raise RuntimeError("benchmark fixture must resolve to READY")

    for _ in range(min(100, iterations)):
        packet = _evaluate_once()
        if packet.packet_hash != expected.packet_hash:
            raise RuntimeError("packet hash changed during warmup")

    samples: list[dict[str, float | int]] = []
    for repeat in range(1, repeats + 1):
        gc.collect()
        started = perf_counter_ns()
        for _ in range(iterations):
            packet = _evaluate_once()
        elapsed_ns = perf_counter_ns() - started
        if packet.packet_hash != expected.packet_hash:
            raise RuntimeError("packet hash changed during benchmark")
        samples.append(
            {
                "repeat": repeat,
                "elapsed_ns": elapsed_ns,
                "packets_per_second": iterations * 1_000_000_000 / elapsed_ns,
            }
        )

    rates = [float(sample["packets_per_second"]) for sample in samples]
    return {
        "schema_version": 1,
        "benchmark": "proofline-deterministic-evaluate",
        "architecture": platform.machine(),
        "operating_system": platform.system(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "iterations_per_repeat": iterations,
        "repeats": repeats,
        "decision": expected.decision,
        "packet_hash": expected.packet_hash,
        "median_packets_per_second": median(rates),
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output")
    args = parser.parse_args()
    rendered = json.dumps(
        benchmark(iterations=args.iterations, repeats=args.repeats),
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
