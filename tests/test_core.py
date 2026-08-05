from datetime import datetime, timedelta, timezone
import unittest

from proofline import Evidence, Requirement, evaluate


NOW = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)


class EvaluateTests(unittest.TestCase):
    def test_missing_evidence_cannot_be_ready(self):
        result = evaluate([Requirement("deploy", "Deployment works")], [], now=NOW)
        self.assertEqual(result.decision, "NEEDS_EVIDENCE")
        self.assertEqual(result.unmet, ("deploy",))

    def test_stale_evidence_is_rejected(self):
        requirement = Requirement("open", "Task is open", max_age_hours=2)
        evidence = Evidence(
            "open",
            "official",
            NOW - timedelta(hours=3),
            "PASS",
            "open",
        )
        result = evaluate([requirement], [evidence], now=NOW)
        self.assertEqual(result.decision, "NEEDS_EVIDENCE")

    def test_conflicting_authorities_are_escalated(self):
        requirement = Requirement("paid", "Payment is funded")
        evidence = [
            Evidence("paid", "ledger-a", NOW, "PASS", "funded"),
            Evidence("paid", "ledger-b", NOW, "FAIL", "unpaid"),
        ]
        result = evaluate([requirement], evidence, now=NOW)
        self.assertEqual(result.decision, "CONFLICT")
        self.assertEqual(result.conflicts, ("paid",))

    def test_non_authoritative_evidence_cannot_satisfy_requirement(self):
        evidence = Evidence(
            "open",
            "unverified-listing",
            NOW,
            "PASS",
            "open",
            authoritative=False,
        )
        result = evaluate([Requirement("open", "Task is open")], [evidence], now=NOW)
        self.assertEqual(result.decision, "NEEDS_EVIDENCE")

    def test_external_action_requires_human_approval(self):
        evidence = Evidence("tested", "ci", NOW, "PASS", "12 tests passed")
        result = evaluate(
            [Requirement("tested", "Tests pass")],
            [evidence],
            now=NOW,
            external_action_requested=True,
            human_approved=False,
        )
        self.assertEqual(result.decision, "APPROVAL_REQUIRED")

    def test_approved_complete_packet_is_ready_and_stable(self):
        requirement = Requirement("tested", "Tests pass")
        evidence = Evidence("tested", "ci", NOW, "PASS", "12 tests passed")
        first = evaluate(
            [requirement],
            [evidence],
            now=NOW,
            external_action_requested=True,
            human_approved=True,
        )
        second = evaluate(
            [requirement],
            [evidence],
            now=NOW,
            external_action_requested=True,
            human_approved=True,
        )
        self.assertEqual(first.decision, "READY")
        self.assertEqual(first.packet_hash, second.packet_hash)


if __name__ == "__main__":
    unittest.main()

