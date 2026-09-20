from __future__ import annotations

import dataclasses
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pagerduty_auto_ack import cli


def make_config(**overrides):
    config = cli.Config(
        api_base_url="https://api.pagerduty.com",
        auth_header="Token token=test",
        user_id="PUSER",
        from_email="user@example.com",
        apply=False,
        interval_seconds=30,
        request_timeout_seconds=20,
        max_pages=10,
        service_ids=[],
        team_ids=[],
        escalation_policy_ids=[],
        schedule_ids=[],
        quiet=True,
    )
    return dataclasses.replace(config, **overrides)


class FakeClient:
    def __init__(self):
        self.acknowledged = []

    def paginate(self, path, collection_key, *, params=None):
        if path == "/oncalls":
            return [
                {
                    "user": {"id": "PUSER"},
                    "start": "2026-01-01T00:00:00Z",
                    "end": "2027-01-01T00:00:00Z",
                    "escalation_policy": {"summary": "Primary"},
                }
            ]
        if path == "/incidents":
            return [
                {
                    "id": "PINCIDENT",
                    "incident_number": 42,
                    "title": "Test incident",
                    "status": "triggered",
                    "assignments": [{"assignee": {"id": "PUSER"}}],
                }
            ]
        raise AssertionError(f"Unexpected path: {path}")

    def acknowledge_incident(self, incident_id):
        self.acknowledged.append(incident_id)
        return {}


class CliTests(unittest.TestCase):
    def test_build_auth_header_accepts_plain_token(self):
        self.assertEqual(cli.build_auth_header("abc123"), "Token token=abc123")

    def test_build_auth_header_rejects_placeholder(self):
        with self.assertRaises(cli.ConfigError):
            cli.build_auth_header("REPLACE_WITH_PAGERDUTY_TOKEN")

    def test_oncall_time_window_is_enforced(self):
        oncall = {
            "user": {"id": "PUSER"},
            "start": "2026-08-09T09:00:00Z",
            "end": "2026-08-09T17:00:00Z",
        }
        now = datetime(2026, 8, 9, 10, 0, tzinfo=timezone.utc)
        later = datetime(2026, 8, 9, 18, 0, tzinfo=timezone.utc)

        self.assertTrue(cli.oncall_is_active_for_user(oncall, "PUSER", now))
        self.assertFalse(cli.oncall_is_active_for_user(oncall, "PUSER", later))
        self.assertFalse(cli.oncall_is_active_for_user(oncall, "POTHER", now))

    def test_dry_run_does_not_acknowledge(self):
        fake_client = FakeClient()
        config = make_config(apply=False)

        acknowledged = cli.run_once(fake_client, config)

        self.assertEqual(acknowledged, 1)
        self.assertEqual(fake_client.acknowledged, [])

    def test_apply_acknowledges_triggered_incident(self):
        fake_client = FakeClient()
        config = make_config(apply=True)

        acknowledged = cli.run_once(fake_client, config)

        self.assertEqual(acknowledged, 1)
        self.assertEqual(fake_client.acknowledged, ["PINCIDENT"])

    def test_legacy_args_are_normalized_to_run_command(self):
        self.assertEqual(
            cli.normalize_argv(["--env-file", ".env", "--once"]),
            ["run", "--env-file", ".env", "--once"],
        )

    def test_init_creates_private_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = os.path.join(temp_dir, "pd-auto-ack.env")

            created_path = cli.create_env_file(env_path)

            self.assertEqual(created_path, env_path)
            with open(env_path, "r", encoding="utf-8") as env_file:
                content = env_file.read()
            self.assertIn("PD_API_TOKEN=REPLACE_WITH_PAGERDUTY_TOKEN", content)
            self.assertEqual(os.stat(env_path).st_mode & 0o777, 0o600)

    def test_init_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = os.path.join(temp_dir, "pd-auto-ack.env")
            cli.create_env_file(env_path)

            with self.assertRaises(cli.ConfigError):
                cli.create_env_file(env_path)

            created_path = cli.create_env_file(env_path, force=True)
            self.assertEqual(created_path, env_path)


if __name__ == "__main__":
    unittest.main()
