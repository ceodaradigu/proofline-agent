import unittest

from benchmarks.arm_optimization_benchmark import benchmark


class ArmOptimizationBenchmarkTests(unittest.TestCase):
    def test_comparison_preserves_packet_and_reports_both_rates(self):
        result = benchmark(
            iterations=2,
            repeats=2,
            requirement_count=4,
            evidence_per_requirement=2,
        )

        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["requirement_count"], 4)
        self.assertEqual(result["evidence_count"], 8)
        self.assertGreater(result["baseline_median_packets_per_second"], 0)
        self.assertGreater(result["optimized_median_packets_per_second"], 0)
        self.assertGreater(result["speedup"], 0)
        self.assertEqual(len(result["packet_hash"]), 64)

    def test_rejects_non_positive_dimensions(self):
        with self.assertRaises(ValueError):
            benchmark(
                iterations=0,
                repeats=1,
                requirement_count=1,
                evidence_per_requirement=1,
            )


if __name__ == "__main__":
    unittest.main()
