"""ADK tools backed by the deterministic Proofline core."""

from __future__ import annotations

from datetime import datetime
import json

from .core import Evidence, Requirement, evaluate


def evaluate_packet(packet_json: str) -> dict[str, object]:
    """Evaluate a JSON task packet and return the deterministic decision.

    Args:
        packet_json: JSON containing requirements, evidence, evaluated_at,
            external_action_requested, and human_approved.
    """

    raw = json.loads(packet_json)
    requirements = [Requirement(**item) for item in raw["requirements"]]
    evidence = [
        Evidence(
            **{
                **item,
                "observed_at": datetime.fromisoformat(item["observed_at"]),
            }
        )
        for item in raw.get("evidence", [])
    ]
    result = evaluate(
        requirements,
        evidence,
        now=datetime.fromisoformat(raw["evaluated_at"]),
        external_action_requested=raw.get("external_action_requested", False),
        human_approved=raw.get("human_approved", False),
    )
    return result.to_dict()

