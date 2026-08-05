"""Deterministic acceptance gate used by the Proofline agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Iterable, Literal


EvidenceState = Literal["PASS", "FAIL"]
Decision = Literal[
    "READY",
    "NEEDS_EVIDENCE",
    "CONFLICT",
    "APPROVAL_REQUIRED",
]


@dataclass(frozen=True)
class Requirement:
    id: str
    statement: str
    max_age_hours: int = 24


@dataclass(frozen=True)
class Evidence:
    requirement_id: str
    source: str
    observed_at: datetime
    state: EvidenceState
    excerpt: str
    authoritative: bool = True


@dataclass(frozen=True)
class ProofPacket:
    decision: Decision
    unmet: tuple[str, ...]
    conflicts: tuple[str, ...]
    evidence_count: int
    external_action_requested: bool
    human_approved: bool
    packet_hash: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("observed_at must include a timezone")
    return value.astimezone(timezone.utc)


def _canonical_payload(
    requirements: tuple[Requirement, ...],
    evidence: tuple[Evidence, ...],
    now: datetime,
    external_action_requested: bool,
    human_approved: bool,
) -> bytes:
    payload = {
        "requirements": [asdict(item) for item in requirements],
        "evidence": [
            {
                **asdict(item),
                "observed_at": _utc(item.observed_at).isoformat(),
            }
            for item in evidence
        ],
        "evaluated_at": _utc(now).isoformat(),
        "external_action_requested": external_action_requested,
        "human_approved": human_approved,
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def evaluate(
    requirements: Iterable[Requirement],
    evidence: Iterable[Evidence],
    *,
    now: datetime | None = None,
    external_action_requested: bool = False,
    human_approved: bool = False,
) -> ProofPacket:
    """Evaluate evidence without allowing an LLM to override acceptance rules."""

    checked_at = _utc(now or datetime.now(timezone.utc))
    requirement_items = tuple(requirements)
    evidence_items = tuple(evidence)

    if not requirement_items:
        raise ValueError("at least one requirement is required")
    ids = [item.id for item in requirement_items]
    if any(not item_id.strip() for item_id in ids):
        raise ValueError("requirement ids must be non-empty")
    if len(ids) != len(set(ids)):
        raise ValueError("requirement ids must be unique")

    unmet: list[str] = []
    conflicts: list[str] = []

    for requirement in requirement_items:
        if requirement.max_age_hours <= 0:
            raise ValueError("max_age_hours must be positive")

        fresh = []
        for item in evidence_items:
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

    if conflicts:
        decision: Decision = "CONFLICT"
    elif unmet:
        decision = "NEEDS_EVIDENCE"
    elif external_action_requested and not human_approved:
        decision = "APPROVAL_REQUIRED"
    else:
        decision = "READY"

    digest = sha256(
        _canonical_payload(
            requirement_items,
            evidence_items,
            checked_at,
            external_action_requested,
            human_approved,
        )
    ).hexdigest()
    return ProofPacket(
        decision=decision,
        unmet=tuple(unmet),
        conflicts=tuple(conflicts),
        evidence_count=len(evidence_items),
        external_action_requested=external_action_requested,
        human_approved=human_approved,
        packet_hash=digest,
    )

