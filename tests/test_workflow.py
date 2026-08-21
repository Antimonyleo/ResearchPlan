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

from common import add_passing_reviews, complete_state

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
        state["campaign"]["resources_dispatch"]["max_concurrency"] = 2
        state["campaign"]["resources_dispatch"]["approvals"] = [
            {"id": "approval-1", "description": "Human authorization for the bounded root unit"}
        ]
        state["campaign"]["work_units"] = [
            {
                "id": "u1", "objective": "authorized evidence pass", "authoritative_inputs": ["campaign"],
                "permitted_actions": ["read"], "prohibited_actions": ["external write"],
                "outputs": ["artifact"], "acceptance_test": "artifact exists and is reviewed",
                "resource_ceiling": "one worker-hour", "retry_policy": "two retries", "retry_limit": 2,
                "escalation": "campaign lead", "dependency_ids": [], "approval_ids": ["approval-1"],
                "external_action_ids": [],
            },
            {
                "id": "u2", "objective": "synthesize", "authoritative_inputs": ["u1 artifact"],
                "permitted_actions": ["read", "write local artifact"], "prohibited_actions": ["publish"],
                "outputs": ["synthesis"], "acceptance_test": "synthesis hash recorded",
                "resource_ceiling": "one worker-hour", "retry_policy": "one retry", "retry_limit": 1,
                "escalation": "campaign lead", "dependency_ids": ["u1"], "approval_ids": [],
                "external_action_ids": [],
            },
        ]
        add_passing_reviews(state)
        # The queue checks this rendered assertion and independently reruns validation.
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
            state["reviews"] = {"frozen_content_digest": "", "rubric_digest": "", "records": []}
            path.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(path), "--db", str(root / "w.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("review.missing", result.stderr + result.stdout)

    def test_init_refuses_a_forged_execution_ready_status_and_stale_reviews(self):
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            path = self.campaign_file(root)
            state = json.loads(path.read_text())
            state["campaign"]["mission"]["scope"] = "Changed after review"
            state["status"] = "execution-ready"
            path.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(path), "--db", str(root / "w.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("review.missing", result.stderr + result.stdout)

    def test_init_rejects_a_dependency_cycle(self):
        """Otherwise the queue accepts it and then never claims anything: silent deadlock."""
        with tempfile.TemporaryDirectory() as temp_str:
            root = Path(temp_str)
            path = self.campaign_file(root)
            state = json.loads(path.read_text())
            units = state["campaign"]["work_units"]
            units[0]["dependency_ids"] = ["u2"]
            add_passing_reviews(state)
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
            # Confirm readiness, then claim through the public transaction path.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM work_units WHERE id='u1'").fetchone()
            spec = json.loads(row["spec_json"])
            ready, _ = workflow.unit_ready(db, spec)
            self.assertTrue(ready)
            db.execute("COMMIT")
            claimed_out = io.StringIO()
            with contextlib.redirect_stdout(claimed_out):
                workflow.cmd_claim(argparse.Namespace(
                    db=str(db_path), worker="worker", lease_seconds=900, max_concurrency=None,
                ))
            token = json.loads(claimed_out.getvalue())["lease_token"]
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
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["work_units"] = [{
                "id": "only", "objective": "one job", "authoritative_inputs": ["campaign"],
                "permitted_actions": ["read"], "prohibited_actions": ["external write"],
                "outputs": ["artifact"], "acceptance_test": "artifact hash", "resource_ceiling": "bounded",
                "retry_policy": "none", "retry_limit": 0, "escalation": "lead", "dependency_ids": [], "approval_ids": [],
                "external_action_ids": [],
            }]
            add_passing_reviews(state)
            state["status"] = "execution-ready"
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

    def test_init_rejects_unknown_or_unbound_approval_ids(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["work_units"][0]["approval_ids"] = ["invented-approval"]
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(campaign), "--db", str(temp / "unknown.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approval", (result.stdout + result.stderr).lower())

            state = json.loads(self.campaign_file(temp).read_text())
            state["campaign"]["ethics_rights_safety"]["external_actions"] = [{
                "id": "publish", "action": "Publish outside the workspace", "approval_id": "approval-1",
            }]
            state["campaign"]["work_units"][0]["external_action_ids"] = ["publish"]
            state["campaign"]["work_units"][0]["approval_ids"] = []
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            result = run_workflow(["init", "--campaign", str(campaign), "--db", str(temp / "unbound.sqlite")])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approval", (result.stdout + result.stderr).lower())

    def test_claim_cannot_raise_campaign_concurrency(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["resources_dispatch"]["max_concurrency"] = 1
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            raised = run_workflow([
                "claim", "--db", str(db_path), "--worker", "w", "--max-concurrency", "2",
            ])
            self.assertNotEqual(raised.returncode, 0)
            self.assertIn("cannot raise campaign ceiling", raised.stdout + raised.stderr)
            claimed = run_workflow(["claim", "--db", str(db_path), "--worker", "w"])
            self.assertEqual(claimed.returncode, 0)
            self.assertTrue(json.loads(claimed.stdout)["claimed"])

    def test_expired_lease_exhausts_retry_limit(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["work_units"][0]["retry_limit"] = 0
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            claim = run_workflow(["claim", "--db", str(db_path), "--worker", "w"])
            self.assertTrue(json.loads(claim.stdout)["claimed"])
            db = workflow.connect(db_path)
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE work_units SET lease_expires='2000-01-01T00:00:00+00:00' WHERE id='u1'")
            workflow.event(db, "test.lease_expired", "u1", {"lease_expires": "2000-01-01T00:00:00+00:00"})
            db.execute("COMMIT")
            reconciled = run_workflow(["reconcile", "--db", str(db_path)])
            self.assertEqual(reconciled.returncode, 0)
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "failed")

    def test_claim_enforces_structured_work_unit_deadline(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["work_units"][0]["deadline_at"] = "2000-01-01T00:00:00+00:00"
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            result = run_workflow(["claim", "--db", str(db_path), "--worker", "w"])
            self.assertEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)["claimed"])
            db = workflow.connect(db_path)
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "failed")

    def test_claim_accepts_a_utc_z_deadline_on_python_39(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            state = json.loads(campaign.read_text())
            state["campaign"]["work_units"][0]["deadline_at"] = "2999-01-01T00:00:00Z"
            add_passing_reviews(state)
            campaign.write_text(json.dumps(state), encoding="utf-8")
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            claim = run_workflow(["claim", "--db", str(db_path), "--worker", "worker"])
            self.assertEqual(claim.returncode, 0, claim.stdout + claim.stderr)
            self.assertTrue(json.loads(claim.stdout)["claimed"])

    def test_claim_rechecks_dependency_artifacts_in_same_transaction(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            first = json.loads(run_workflow(["claim", "--db", str(db_path), "--worker", "w1"]).stdout)
            artifact = temp / "u1.txt"
            artifact.write_text("verified", encoding="utf-8")
            completed = run_workflow([
                "complete", "--db", str(db_path), "--unit", "u1", "--token", first["lease_token"],
                "--artifact", str(artifact), "--acceptance-evidence", "checked",
            ])
            self.assertEqual(completed.returncode, 0)
            artifact.write_text("tampered", encoding="utf-8")
            second = run_workflow(["claim", "--db", str(db_path), "--worker", "w2"])
            self.assertEqual(second.returncode, 0)
            payload = json.loads(second.stdout)
            self.assertFalse(payload["claimed"])
            self.assertIn("integrity failed", json.dumps(payload))
            db = workflow.connect(db_path)
            self.assertEqual(db.execute("SELECT status FROM work_units WHERE id='u1'").fetchone()["status"], "blocked")
            audited = run_workflow(["audit", "--db", str(db_path)])
            self.assertEqual(audited.returncode, 2)
            self.assertTrue(json.loads(audited.stdout)["artifact_problems"])

    def test_audit_rejects_uninitialized_and_tampered_event_history(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            empty = run_workflow(["audit", "--db", str(temp / "empty.sqlite")])
            self.assertNotEqual(empty.returncode, 0)
            self.assertIn("not initialized", empty.stdout + empty.stderr)

            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            self.assertEqual(run_workflow(["audit", "--db", str(db_path)]).returncode, 0)
            db = workflow.connect(db_path)
            db.execute("DELETE FROM events WHERE seq=(SELECT MAX(seq) FROM events)")
            truncated = run_workflow(["audit", "--db", str(db_path)])
            self.assertEqual(truncated.returncode, 2)
            self.assertFalse(json.loads(truncated.stdout)["valid"])

    def test_audit_rejects_reordered_event_history(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            db = workflow.connect(db_path)
            seqs = [row["seq"] for row in db.execute("SELECT seq FROM events ORDER BY seq").fetchall()]
            self.assertEqual(len(seqs), 2)
            db.execute("UPDATE events SET seq=-1 WHERE seq=?", (seqs[0],))
            db.execute("UPDATE events SET seq=? WHERE seq=?", (seqs[0], seqs[1]))
            db.execute("UPDATE events SET seq=? WHERE seq=-1", (seqs[1],))
            reordered = run_workflow(["audit", "--db", str(db_path)])
            self.assertEqual(reordered.returncode, 2)
            self.assertFalse(json.loads(reordered.stdout)["valid"])

    def test_state_changes_refuse_tampered_event_history_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            self.assertEqual(run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "owner", "--evidence", "ticket-1",
            ]).returncode, 0)
            claimed = json.loads(run_workflow([
                "claim", "--db", str(db_path), "--worker", "worker-1",
            ]).stdout)
            self.assertTrue(claimed["claimed"])

            db = workflow.connect(db_path)
            db.execute("UPDATE work_units SET lease_expires='2000-01-01T00:00:00+00:00' WHERE id='u1'")
            db.execute("DELETE FROM events WHERE seq=(SELECT MAX(seq) FROM events)")

            def snapshot():
                return {
                    "meta": [tuple(row) for row in db.execute("SELECT * FROM meta ORDER BY key")],
                    "units": [tuple(row) for row in db.execute("SELECT * FROM work_units ORDER BY id")],
                    "approvals": [tuple(row) for row in db.execute("SELECT * FROM approvals ORDER BY id")],
                    "events": [tuple(row) for row in db.execute("SELECT * FROM events ORDER BY seq")],
                }

            before = snapshot()
            approval = run_workflow([
                "approve", "--db", str(db_path), "--approval", "approval-1",
                "--by", "attacker", "--evidence", "replacement",
            ])
            self.assertNotEqual(approval.returncode, 0)
            self.assertIn("event history", approval.stdout + approval.stderr)
            self.assertEqual(snapshot(), before)

            claim = run_workflow(["claim", "--db", str(db_path), "--worker", "worker-2"])
            self.assertNotEqual(claim.returncode, 0)
            self.assertIn("event history", claim.stdout + claim.stderr)
            self.assertEqual(snapshot(), before)

    def test_claim_and_audit_reject_unlogged_queue_state_changes(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            campaign = self.campaign_file(temp)
            db_path = temp / "workflow.sqlite"
            self.assertEqual(run_workflow(["init", "--campaign", str(campaign), "--db", str(db_path)]).returncode, 0)
            db = workflow.connect(db_path)
            db.execute(
                "UPDATE approvals SET status='approved',approved_by='sql',evidence='unlogged' "
                "WHERE id='approval-1'"
            )
            before = [tuple(row) for row in db.execute("SELECT * FROM work_units ORDER BY id")]

            claim = run_workflow(["claim", "--db", str(db_path), "--worker", "worker"])
            self.assertNotEqual(claim.returncode, 0)
            self.assertIn("event history", claim.stdout + claim.stderr)
            self.assertEqual(
                [tuple(row) for row in db.execute("SELECT * FROM work_units ORDER BY id")], before
            )
            audited = run_workflow(["audit", "--db", str(db_path)])
            self.assertEqual(audited.returncode, 2)
            self.assertIn("state_mismatch", audited.stdout)

    def test_state_projection_covers_meta_and_work_unit_specs(self):
        mutations = {
            "meta": "UPDATE meta SET value='true' WHERE key='stopped'",
            "work unit spec": "UPDATE work_units SET spec_json=spec_json || ' ' WHERE id='u1'",
        }
        for label, statement in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_str:
                temp = Path(temp_str)
                campaign = self.campaign_file(temp)
                db_path = temp / "workflow.sqlite"
                self.assertEqual(run_workflow([
                    "init", "--campaign", str(campaign), "--db", str(db_path),
                ]).returncode, 0)
                db = workflow.connect(db_path)
                db.execute(statement)

                claim = run_workflow(["claim", "--db", str(db_path), "--worker", "worker"])
                self.assertNotEqual(claim.returncode, 0)
                self.assertIn("event history", claim.stdout + claim.stderr)
                audited = run_workflow(["audit", "--db", str(db_path)])
                self.assertEqual(audited.returncode, 2)
                self.assertIn("state_mismatch", audited.stdout)

    def test_corrupt_or_legacy_queue_requires_explicit_replace(self):
        with tempfile.TemporaryDirectory() as temp_str:
            temp = Path(temp_str)
            db_path = temp / "workflow.sqlite"
            uninitialized = run_workflow(["claim", "--db", str(db_path), "--worker", "worker"])
            self.assertNotEqual(uninitialized.returncode, 0)
            self.assertIn("not initialized", uninitialized.stdout + uninitialized.stderr)

            db = workflow.connect(db_path)
            workflow.schema(db)
            db.execute("INSERT INTO meta(key,value) VALUES('campaign_digest','legacy')")
            legacy = run_workflow(["claim", "--db", str(db_path), "--worker", "worker"])
            self.assertNotEqual(legacy.returncode, 0)
            self.assertIn("init --replace", legacy.stdout + legacy.stderr)

            campaign = self.campaign_file(temp)
            replaced = run_workflow([
                "init", "--campaign", str(campaign), "--db", str(db_path), "--replace",
            ])
            self.assertEqual(replaced.returncode, 0, replaced.stdout + replaced.stderr)
            self.assertEqual(run_workflow(["audit", "--db", str(db_path)]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
