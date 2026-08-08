import unittest

from fastapi.testclient import TestClient

from server import app


class PublicServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_is_a_clear_judge_facing_page(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Evidence before", response.text)
        self.assertIn("AI-assisted project and presentation", response.text)
        self.assertIn("NEEDS_EVIDENCE", response.text)
        self.assertIn("APPROVAL_REQUIRED", response.text)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_adk_discovery_remains_available(self):
        response = self.client.get("/list-apps")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["proofline"])


if __name__ == "__main__":
    unittest.main()
