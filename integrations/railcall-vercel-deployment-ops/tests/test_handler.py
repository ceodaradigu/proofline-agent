"""Safety-focused unit tests for the Vercel RailCall handler."""

from __future__ import annotations

import importlib.util
import os
import pathlib
import unittest
from unittest.mock import patch


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vercel_deployment_ops_handler", ROOT / "handlers" / "handler.py"
)
assert SPEC and SPEC.loader
handler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handler)
os.environ.setdefault("VERCEL_ACCESS_TOKEN", "test-token-not-a-secret")


class VercelDeploymentOpsTests(unittest.TestCase):
    def test_project_projection_omits_environment_data(self) -> None:
        response = handler.ApiResult(
            {
                "projects": [
                    {
                        "id": "prj_1",
                        "name": "demo",
                        "framework": "nextjs",
                        "env": [{"key": "SECRET", "value": "must-not-leak"}],
                    }
                ],
                "pagination": {"count": 1, "next": None},
            },
            200,
            1,
        )
        with patch.object(handler, "_request", return_value=response):
            output = handler.list_projects({}, {})
        self.assertEqual(output["projects"][0]["name"], "demo")
        self.assertNotIn("env", output["projects"][0])
        self.assertNotIn("must-not-leak", repr(output))

    def test_event_receipts_hash_and_omit_log_content(self) -> None:
        response = handler.ApiResult(
            [{"id": "evt_1", "type": "stdout", "created": 123, "text": "secretish log"}],
            200,
            1,
        )
        with patch.object(handler, "_request", return_value=response):
            output = handler.get_deployment_events(
                {"deployment_id_or_url": "dpl_1"}, {}
            )
        self.assertTrue(output["content_omitted_from_receipt"])
        self.assertEqual(len(output["events"][0]["content_sha256"]), 64)
        self.assertNotIn("secretish log", repr(output))

    def test_deployment_projection_omits_git_metadata(self) -> None:
        response = handler.ApiResult(
            {
                "deployments": [
                    {
                        "uid": "dpl_1",
                        "name": "demo",
                        "url": "demo.vercel.app",
                        "readyState": "READY",
                        "creator": {"uid": "usr_1", "username": "operator", "email": "private@example.com"},
                        "meta": {
                            "githubCommitMessage": "do not copy this into a receipt",
                            "githubCommitSha": "abc123",
                            "githubRepo": "private-repository",
                        },
                    }
                ],
                "pagination": {"count": 1},
            },
            200,
            1,
        )
        with patch.object(handler, "_request", return_value=response):
            output = handler.list_deployments({}, {})
        deployment = output["deployments"][0]
        self.assertNotIn("meta", deployment)
        self.assertEqual(deployment["creator"], {"uid": "usr_1", "username": "operator"})
        self.assertNotIn("private@example.com", repr(output))
        self.assertNotIn("private-repository", repr(output))

    def test_cancel_refuses_stale_state_without_writing(self) -> None:
        current = handler.ApiResult(
            {"id": "dpl_1", "url": "demo.vercel.app", "readyState": "READY"},
            200,
            1,
        )
        with patch.object(handler, "_get_deployment_result", return_value=current), patch.object(
            handler, "_request"
        ) as write:
            with self.assertRaisesRegex(RuntimeError, "Refusing stale cancellation"):
                handler.cancel_deployment(
                    {"deployment_id": "dpl_1", "expected_ready_state": "BUILDING"},
                    {},
                )
        write.assert_not_called()

    def test_cancel_verifies_terminal_state(self) -> None:
        before = handler.ApiResult(
            {"id": "dpl_1", "url": "demo.vercel.app", "readyState": "BUILDING"},
            200,
            1,
        )
        after = handler.ApiResult(
            {"id": "dpl_1", "url": "demo.vercel.app", "readyState": "CANCELED"},
            200,
            1,
        )
        with patch.object(handler, "_get_deployment_result", return_value=before), patch.object(
            handler, "_request", return_value=handler.ApiResult({}, 200, 1)
        ), patch.object(handler, "_poll_deployment_state", return_value=after):
            output = handler.cancel_deployment(
                {"deployment_id": "dpl_1", "expected_ready_state": "BUILDING"},
                {},
            )
        self.assertTrue(output["changed"])
        self.assertEqual(output["after"]["readyState"], "CANCELED")

    def test_delete_refuses_wrong_url_without_writing(self) -> None:
        current = handler.ApiResult(
            {
                "id": "dpl_1",
                "url": "right.vercel.app",
                "createdAt": 123456,
                "readyState": "READY",
            },
            200,
            1,
        )
        with patch.object(handler, "_get_deployment_result", return_value=current), patch.object(
            handler, "_request"
        ) as write:
            with self.assertRaisesRegex(RuntimeError, "confirm_deployment_url"):
                handler.delete_deployment(
                    {
                        "deployment_id": "dpl_1",
                        "confirm_deployment_url": "wrong.vercel.app",
                        "expected_created_at": 123456,
                    },
                    {},
                )
        write.assert_not_called()

    def test_delete_requires_authoritative_404(self) -> None:
        current = handler.ApiResult(
            {
                "id": "dpl_1",
                "url": "right.vercel.app",
                "createdAt": 123456,
                "readyState": "READY",
            },
            200,
            1,
        )
        with patch.object(handler, "_get_deployment_result", return_value=current), patch.object(
            handler,
            "_request",
            side_effect=[
                handler.ApiResult({}, 200, 1),
                handler.ApiResult(None, 404, 1),
            ],
        ):
            output = handler.delete_deployment(
                {
                    "deployment_id": "dpl_1",
                    "confirm_deployment_url": "right.vercel.app",
                    "expected_created_at": 123456,
                },
                {},
            )
        self.assertTrue(output["deleted"])
        self.assertEqual(output["attempts"], 3)


if __name__ == "__main__":
    unittest.main()
