from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ContainerContractTests(unittest.TestCase):
    def test_cloud_run_container_uses_runtime_port_and_adk_server(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("adk api_server", dockerfile)
        self.assertIn('--port \\"$PORT\\"', dockerfile)
        self.assertIn("/app/agents", dockerfile)

    def test_container_never_copies_local_secrets(self):
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

        self.assertIn(".env", dockerignore.splitlines())
        self.assertIn(".git", dockerignore.splitlines())
        self.assertIn("video", dockerignore.splitlines())


if __name__ == "__main__":
    unittest.main()
