"""Run a synthetic Proofline decision without cloud credentials."""

from datetime import datetime, timedelta, timezone
import json

from proofline import Evidence, Requirement, evaluate


now = datetime.now(timezone.utc).replace(microsecond=0)
requirements = (
    Requirement("source-open", "Authoritative source confirms the task is open"),
    Requirement("payment-funded", "Reward is funded and collectible"),
    Requirement("deliverable-tested", "Deliverable passes its acceptance test"),
)
evidence = (
    Evidence("source-open", "official-source", now, "PASS", "Status: open"),
    Evidence("payment-funded", "payment-ledger", now, "PASS", "Escrow: funded"),
    Evidence(
        "deliverable-tested",
        "ci-run",
        now - timedelta(minutes=2),
        "PASS",
        "12 tests passed",
    ),
)

packet = evaluate(
    requirements,
    evidence,
    now=now,
    external_action_requested=True,
    human_approved=False,
)
print(json.dumps(packet.to_dict(), indent=2, sort_keys=True))

