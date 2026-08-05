"""Render a deterministic four-state Proofline demo for judges and reviewers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

from proofline import Evidence, Requirement, evaluate


DEMO_TIME = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)


def build_demo_matrix() -> list[dict[str, object]]:
    """Return one reproducible packet for every Proofline decision state."""

    requirement = Requirement("release", "Release is verified", max_age_hours=2)
    passing = Evidence(
        "release",
        "ci.example/run/42",
        DEMO_TIME - timedelta(minutes=5),
        "PASS",
        "tests passed",
    )

    cases = [
        (
            "missing evidence",
            evaluate([requirement], [], now=DEMO_TIME),
        ),
        (
            "conflicting authorities",
            evaluate(
                [requirement],
                [
                    passing,
                    Evidence(
                        "release",
                        "deploy.example/health",
                        DEMO_TIME - timedelta(minutes=2),
                        "FAIL",
                        "service unavailable",
                    ),
                ],
                now=DEMO_TIME,
            ),
        ),
        (
            "approval boundary",
            evaluate(
                [requirement],
                [passing],
                now=DEMO_TIME,
                external_action_requested=True,
                human_approved=False,
            ),
        ),
        (
            "approved completion",
            evaluate(
                [requirement],
                [passing],
                now=DEMO_TIME,
                external_action_requested=True,
                human_approved=True,
            ),
        ),
    ]

    return [{"scenario": name, **packet.to_dict()} for name, packet in cases]


def main() -> None:
    print(json.dumps(build_demo_matrix(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
