import unittest

from demo_matrix import build_demo_matrix


class DemoMatrixTests(unittest.TestCase):
    def test_matrix_covers_every_decision_state_in_order(self):
        packets = build_demo_matrix()

        self.assertEqual(
            [packet["decision"] for packet in packets],
            ["NEEDS_EVIDENCE", "CONFLICT", "APPROVAL_REQUIRED", "READY"],
        )
        self.assertEqual(len({packet["packet_hash"] for packet in packets}), 4)


if __name__ == "__main__":
    unittest.main()
