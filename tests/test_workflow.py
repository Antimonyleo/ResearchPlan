from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
import contextlib
import io
import concurrent.futures
import subprocess
import sys
from pathlib import Path

from common import complete_state

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("rescamp_workflow", ROOT / "rescamp/scripts/workflow.py")
workflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(workflow)


def run_workflow(argv):
    return subprocess.run([sys.executable, str(ROOT / "rescamp/scripts/workflow.py")] + argv,
                          capture_output=True, text=True)


class WorkflowTests(unittest.TestCase):
    def campaign_file(self, root: Path) -> Path:
        state = complete_state()
        state["campaign"]["runtime"] = {
            "enabled": True,
            "continuation_trigger": "operator or scheduler invokes claim",
            "state_store": "SQLite",
            "event_log": "append-only events table",
            "checkpoint_policy": "commit every state transition",
            "liveness": "leases and heartbeats",
            "recovery": "expire leases and verify artifacts",
            "idempotency": "one work-unit ID and lease token",
        }
        state["campaign"]["work_units"] = [
            {
                "id": "u1", "objective": "authorized evidence pass", "authoritative_inputs": ["campaign"],
                "permitted_actions": ["read"], "prohibited_actions": ["external write"],
                "outputs": ["artifact"], "acceptance_test": "artifact exists and is reviewed",
                "resource_ceiling": "one worker-hour", "retry_policy": "two retries", "retry_limit": 2,
                "escalation": "campaign lead", "dependency_ids": [], "approval_ids": ["approval-1"],
            },
            {
                "id": "u2", "objective": "synthesize", "authoritative_inputs": ["u1 artifact"],
                "permitted_actions": ["read", "write local artifact"], "prohibited_actions": ["publish"],
                "outputs": ["synthesis"], "acceptance_test": "synthesis hash recorded",
                "resource_ceiling": "one worker-hour", "retry_policy": "one retry", "retry_limit": 1,
                "escalation": "campaign lead", "dependency_ids": ["u1"], "approval_ids": [],
            },
        ]
        # The queue only accepts a finalized campaign, so the fixture must be one.
        state["status"] = "execution-ready"
        path = root / "campaign.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        return path

    def test_init_refuses_a_campaign_that_was_never_finalized(self):
        """The one component that dispatches work must not skip the readiness check."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            path = self.campaign_file(root)
            state = json.loads(path.read_text())
            state["status"] = "candidate"
            path.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(path), "--db", str(root / "w.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("execution-ready", result.stderr + result.stdout)

    def test_init_rejects_a_dependency_cycle(self):
        """Otherwise the queue accepts it and then never claims anything: silent deadlock."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            path = self.campaign_file(root)
            state = json.loads(path.read_text())
            units = state["campaign"]["work_units"]
            units[0]["dependency_ids"] = ["u2"]
            path.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(path), "--db", str(root / "w.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cycle", result.stderr + result.stdout)

    def test_fail_closed_approval_dependency_and_artifact_audit(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_init(argparse.Namespace(campaign=str(campaign), db=str(db_path), force=False, replace=False))
            db = workflow.connect(db_path)
            workflow.schema(db)
            # Approval blocks the only root unit.
            db.execute("BEGIN IMMEDIATE")
            try:
                workflow.expire_leases(db)
                row = db.execute("SELECT spec_json FROM work_units WHERE id='u1'").fetchone()
                ready, reason = workflow.unit_ready(db, json.loads(row["spec_json"]))
                self.assertFalse(ready)
                self.assertIn("approval", reason)
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_approve(argparse.Namespace(db=str(db_path), approval="approval-1", by="human-reviewer", evidence="ticket-17"))
            # Claim u1 directly under the same transaction logic used by the CLI.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM work_units WHERE id='u1'").fetchone()
            spec = json.loads(row["spec_json"])
            ready, _ = workflow.unit_ready(db, spec)
            self.assertTrue(ready)
            token = "test-token"
            expiry = "2999-01-01T00:00:00+00:00"
            db.execute("UPDATE work_units SET status='leased',attempts=1,lease_token=?,lease_owner='worker',lease_expires=? WHERE id='u1'", (token, expiry))
            db.execute("COMMIT")
            artifact = temp / "u1.txt"
            artifact.write_text("evidence", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_complete(argparse.Namespace(db=str(db_path), unit="u1", token=token, artifact=[str(artifact)], acceptance_evidence="reviewed against unit acceptance test"))
            row2 = db.execute("SELECT spec_json FROM work_units WHERE id='u2'").fetchone()
            ready2, _ = workflow.unit_ready(db, json.loads(row2["spec_json"]))
            self.assertTrue(ready2)
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "succeeded")
            # Tampering is detected and blocks the completed unit.
            artifact.write_text("tampered", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_reconcile(argparse.Namespace(db=str(db_path)))
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "blocked")


    def test_concurrent_claims_do_not_duplicate_one_unit(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            state = complete_state()
            state["campaign"]["runtime"] = {
                "enabled": True, "continuation_trigger": "operator", "state_store": "SQLite",
                "event_log": "events", "checkpoint_policy": "transaction", "liveness": "lease",
                "recovery": "reconcile", "idempotency": "unit ID",
            }
            state["campaign"]["work_units"] = [{
                "id": "only", "objective": "one job", "authoritative_inputs": ["campaign"],
                "permitted_actions": ["read"], "prohibited_actions": ["external write"],
                "outputs": ["artifact"], "acceptance_test": "artifact hash", "resource_ceiling": "bounded",
                "retry_policy": "none", "retry_limit": 0, "escalation": "lead", "dependency_ids": [], "approval_ids": [],
            }]
            state["status"] = "execution-ready"
            campaign = temp / "campaign.json"
            campaign.write_text(json.dumps(state), encoding="utf-8")
            db = temp / "workflow.sqlite"
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_init(argparse.Namespace(campaign=str(campaign), db=str(db), force=False, replace=False))
            command = [sys.executable, str(ROOT / "rescamp/scripts/workflow.py"), "claim", "--db", str(db), "--worker"]
            def claim(worker):
                return subprocess.run(command + [worker], text=True, capture_output=True, check=False)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(claim, ["w1", "w2"]))
            self.assertTrue(all(item.returncode == 0 for item in results))
            payloads = [json.loads(item.stdout) for item in results]
            self.assertEqual(sum(bool(item["claimed"]) for item in payloads), 1)

    def test_expired_lease_returns_to_pending(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            with contextlib.redirect_stdout(io.StringIO()):
                workflow.cmd_init(argparse.Namespace(campaign=str(campaign), db=str(db_path), force=False, replace=False))
            db = workflow.connect(db_path)
            db.execute("UPDATE work_units SET status='leased',lease_token='x',lease_owner='w',lease_expires='2000-01-01T00:00:00+00:00' WHERE id='u1'")
            self.assertEqual(workflow.expire_leases(db), 1)
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "pending")


if __name__ == "__main__":
    unittest.main()
