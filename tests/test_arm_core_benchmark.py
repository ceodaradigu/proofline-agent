import unittest

from benchmarks.arm_core_benchmark import benchmark


class ArmCoreBenchmarkTests(unittest.TestCase):
    def test_small_run_is_reproducible_and_machine_readable(self):
        result = benchmark(iterations=5, repeats=2)

        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(result["iterations_per_repeat"], 5)
        self.assertEqual(result["repeats"], 2)
        self.assertEqual(len(result["samples"]), 2)
        self.assertEqual(len(result["packet_hash"]), 64)
        self.assertGreater(result["median_packets_per_second"], 0)
        self.assertTrue(
            all(sample["elapsed_ns"] > 0 for sample in result["samples"])
        )

    def test_rejects_non_positive_work(self):
        with self.assertRaises(ValueError):
            benchmark(iterations=0, repeats=1)
        with self.assertRaises(ValueError):
            benchmark(iterations=1, repeats=0)


if __name__ == "__main__":
    unittest.main()
