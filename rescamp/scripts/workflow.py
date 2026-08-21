#!/usr/bin/env python3
"""Optional fail-closed SQLite queue for an already validated ResCamp campaign.

This utility persists bounded work units, leases, approvals, and artifact hashes. It
never calls a model, executes scientific tools, or grants approval. A real worker or
scheduler must invoke it and perform the work described by a claimed unit.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Any

VERSION = "0.8.6"
FINAL = {"succeeded", "failed", "blocked"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA journal_mode=WAL")
    return db


def schema(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS work_units(
      id TEXT PRIMARY KEY, spec_json TEXT NOT NULL, status TEXT NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0, lease_token TEXT, lease_owner TEXT,
      lease_expires TEXT, result_json TEXT, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS approvals(
      id TEXT PRIMARY KEY, status TEXT NOT NULL, approved_by TEXT,
      evidence TEXT, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events(
      seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, type TEXT NOT NULL,
      unit_id TEXT, payload_json TEXT NOT NULL
    );
    """)


def event(db: sqlite3.Connection, kind: str, unit_id: str | None, payload: dict[str, Any]) -> None:
    db.execute("INSERT INTO events(at,type,unit_id,payload_json) VALUES(?,?,?,?)",
               (now(), kind, unit_id, json.dumps(payload, sort_keys=True, ensure_ascii=False)))


def read_campaign(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("campaign", data)


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value)


def expire_leases(db: sqlite3.Connection) -> int:
    rows = db.execute("SELECT id,lease_expires FROM work_units WHERE status='leased'").fetchall()
    current = dt.datetime.now(dt.timezone.utc)
    expired = [row["id"] for row in rows if parse_time(row["lease_expires"]) and parse_time(row["lease_expires"]) <= current]
    for ident in expired:
        db.execute("UPDATE work_units SET status='pending',lease_token=NULL,lease_owner=NULL,lease_expires=NULL,updated_at=? WHERE id=?", (now(), ident))
        event(db, "lease.expired", ident, {})
    return len(expired)


def unit_ready(db: sqlite3.Connection, spec: dict[str, Any]) -> tuple[bool, str]:
    dependencies = spec.get("dependency_ids", [])
    for dep in dependencies:
        row = db.execute("SELECT status FROM work_units WHERE id=?", (dep,)).fetchone()
        if row is None:
            return False, f"unknown dependency {dep}"
        if row["status"] != "succeeded":
            return False, f"dependency {dep} is {row['status']}"
    for approval in spec.get("approval_ids", []):
        row = db.execute("SELECT status FROM approvals WHERE id=?", (approval,)).fetchone()
        if row is None or row["status"] != "approved":
            return False, f"approval {approval} is absent"
    return True, ""


def file_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"artifact is not a file: {path}")
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


def graph_cycle(nodes: set[str], edges: list[tuple[str, str]]) -> list[str]:
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for left, right in edges:
        if left in nodes and right in nodes:
            adjacency[left].append(right)
    visiting: set[str] = set()
    visited: set[str] = set()
    trail: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            return trail[trail.index(node):] + [node]
        if node in visited:
            return None
        visiting.add(node)
        trail.append(node)
        for nxt in adjacency.get(node, []):
            found = visit(nxt)
            if found:
                return found
        trail.pop()
        visiting.discard(node)
        visited.add(node)
        return None

    for node in sorted(nodes):
        found = visit(node)
        if found:
            return found
    return []


def cmd_init(args: argparse.Namespace) -> None:
    campaign_path = Path(args.campaign).resolve()
    source = json.loads(campaign_path.read_text(encoding="utf-8"))
    campaign = source.get("campaign", source)
    runtime = campaign.get("runtime", {})
    if not runtime.get("enabled") and not args.force:
        raise SystemExit("campaign.runtime.enabled is false; use --force only for an intentional dry-run queue")
    # This is the one component that actually dispatches work, so it must not be the one
    # that skips the readiness check. Previously it accepted a campaign with no mission,
    # no reviews, and a NOT EXECUTION-READY bundle.
    status = source.get("status")
    if status != "execution-ready" and not args.force:
        raise SystemExit(
            f"campaign status is {status!r}, not 'execution-ready'.\n"
            "Run `rescamp.py finalize` and pass the campaign.json it renders. "
            "Use --force only for an intentional dry-run queue."
        )
    units = campaign.get("work_units", [])
    if not units:
        raise SystemExit("campaign has no work units")
    ids = [item.get("id") for item in units]
    if any(not ident for ident in ids) or len(ids) != len(set(ids)):
        raise SystemExit("work-unit IDs must be unique and non-empty")
    known = set(ids)
    edges: list[tuple[str, str]] = []
    for unit in units:
        unknown = set(unit.get("dependency_ids", [])) - known
        if unknown:
            raise SystemExit(f"work unit {unit['id']} has unknown dependencies: {sorted(unknown)}")
        for dependency in unit.get("dependency_ids", []):
            edges.append((dependency, unit["id"]))
    cycle = graph_cycle(set(ids), edges)
    if cycle:
        # Without this the queue accepts the campaign and then never claims anything:
        # a silent permanent deadlock discovered only at runtime.
        raise SystemExit("work-unit dependency cycle: " + " -> ".join(cycle))
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        if db.execute("SELECT 1 FROM meta WHERE key='campaign_digest'").fetchone() and not args.replace:
            raise SystemExit("workflow database already initialized; use --replace")
        if args.replace:
            db.execute("DELETE FROM work_units")
            db.execute("DELETE FROM approvals")
            db.execute("DELETE FROM events")
            db.execute("DELETE FROM meta")
        payload = json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        meta = {
            "workflow_version": VERSION,
            "campaign_digest": digest,
            "campaign_path": str(campaign_path),
            "stopped": "false",
            "created_at": now(),
        }
        for key, value in meta.items():
            db.execute("INSERT INTO meta(key,value) VALUES(?,?)", (key, value))
        for unit in units:
            db.execute("INSERT INTO work_units(id,spec_json,status,updated_at) VALUES(?,?,?,?)",
                       (unit["id"], json.dumps(unit, sort_keys=True, ensure_ascii=False), "pending", now()))
            for approval in unit.get("approval_ids", []):
                db.execute("INSERT OR IGNORE INTO approvals(id,status,updated_at) VALUES(?,?,?)", (approval, "pending", now()))
        event(db, "workflow.initialized", None, {"campaign_digest": digest, "work_units": ids, "forced": bool(args.force)})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps({"db": str(Path(args.db).resolve()), "campaign_digest": digest, "work_units": len(units)}, indent=2))


def cmd_claim(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        expire_leases(db)
        stopped = db.execute("SELECT value FROM meta WHERE key='stopped'").fetchone()
        if stopped is None:
            raise SystemExit("workflow is not initialized")
        if stopped["value"] == "true":
            raise SystemExit("workflow is stopped")
        active = db.execute("SELECT COUNT(*) AS n FROM work_units WHERE status='leased'").fetchone()["n"]
        max_concurrency = int(args.max_concurrency)
        if active >= max_concurrency:
            raise SystemExit("concurrency ceiling reached")
        chosen = None
        blocked_reasons = []
        for row in db.execute("SELECT * FROM work_units WHERE status='pending' ORDER BY id").fetchall():
            spec = json.loads(row["spec_json"])
            ready, reason = unit_ready(db, spec)
            if ready:
                chosen = (row, spec)
                break
            blocked_reasons.append({"id": row["id"], "reason": reason})
        if chosen is None:
            db.execute("COMMIT")
            print(json.dumps({"claimed": False, "blocked": blocked_reasons}, indent=2))
            return
        row, spec = chosen
        token = secrets.token_urlsafe(24)
        expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=args.lease_seconds)
        db.execute("UPDATE work_units SET status='leased',attempts=attempts+1,lease_token=?,lease_owner=?,lease_expires=?,updated_at=? WHERE id=? AND status='pending'",
                   (token, args.worker, expiry.isoformat(), now(), row["id"]))
        event(db, "work.claimed", row["id"], {"worker": args.worker, "lease_expires": expiry.isoformat()})
        db.execute("COMMIT")
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    print(json.dumps({"claimed": True, "unit": spec, "lease_token": token, "lease_expires": expiry.isoformat()}, indent=2, ensure_ascii=False))


def leased_row(db: sqlite3.Connection, ident: str, token: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM work_units WHERE id=?", (ident,)).fetchone()
    if row is None:
        raise SystemExit(f"unknown work unit {ident}")
    if row["status"] != "leased" or row["lease_token"] != token:
        raise SystemExit("invalid or stale lease token")
    expiry = parse_time(row["lease_expires"])
    if expiry and expiry <= dt.datetime.now(dt.timezone.utc):
        raise SystemExit("lease expired")
    return row


def cmd_heartbeat(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        leased_row(db, args.unit, args.token)
        expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=args.lease_seconds)
        db.execute("UPDATE work_units SET lease_expires=?,updated_at=? WHERE id=?", (expiry.isoformat(), now(), args.unit))
        event(db, "work.heartbeat", args.unit, {"lease_expires": expiry.isoformat()})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps({"unit": args.unit, "lease_expires": expiry.isoformat()}, indent=2))


def cmd_complete(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    artifacts = [file_record(Path(value)) for value in args.artifact]
    if not artifacts:
        raise SystemExit("at least one artifact is required")
    if not args.acceptance_evidence.strip():
        raise SystemExit("acceptance evidence is required")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = leased_row(db, args.unit, args.token)
        result = {
            "completed_at": now(), "artifacts": artifacts,
            "acceptance": "passed", "acceptance_evidence": args.acceptance_evidence,
            "worker": row["lease_owner"],
        }
        db.execute("UPDATE work_units SET status='succeeded',lease_token=NULL,lease_owner=NULL,lease_expires=NULL,result_json=?,updated_at=? WHERE id=?",
                   (json.dumps(result, sort_keys=True, ensure_ascii=False), now(), args.unit))
        event(db, "work.completed", args.unit, result)
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_fail(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        row = leased_row(db, args.unit, args.token)
        spec = json.loads(row["spec_json"])
        limit = int(spec.get("retry_limit", args.default_retry_limit))
        retry = bool(args.retryable and row["attempts"] <= limit)
        status = "pending" if retry else "failed"
        result = {"failed_at": now(), "reason": args.reason, "retryable": bool(args.retryable), "requeued": retry, "attempts": row["attempts"], "retry_limit": limit}
        db.execute("UPDATE work_units SET status=?,lease_token=NULL,lease_owner=NULL,lease_expires=NULL,result_json=?,updated_at=? WHERE id=?",
                   (status, json.dumps(result, sort_keys=True, ensure_ascii=False), now(), args.unit))
        event(db, "work.failed", args.unit, result)
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps(result, indent=2))


def cmd_approve(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT id FROM approvals WHERE id=?", (args.approval,)).fetchone()
        if row is None:
            raise SystemExit(f"unknown approval {args.approval}")
        db.execute("UPDATE approvals SET status='approved',approved_by=?,evidence=?,updated_at=? WHERE id=?",
                   (args.by, args.evidence, now(), args.approval))
        event(db, "approval.granted", None, {"approval": args.approval, "approved_by": args.by, "evidence": args.evidence})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(args.approval)


def cmd_stop(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    value = "false" if args.resume else "true"
    db.execute("BEGIN IMMEDIATE")
    try:
        if not db.execute("SELECT 1 FROM meta WHERE key='campaign_digest'").fetchone():
            raise SystemExit("workflow is not initialized")
        db.execute("INSERT INTO meta(key,value) VALUES('stopped',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (value,))
        event(db, "workflow.resumed" if args.resume else "workflow.stopped", None, {"reason": args.reason})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print("resumed" if args.resume else "stopped")


def cmd_reconcile(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    problems = []
    try:
        expired = expire_leases(db)
        for row in db.execute("SELECT id,result_json FROM work_units WHERE status IN ('succeeded','blocked')").fetchall():
            result = json.loads(row["result_json"] or "{}")
            for artifact in result.get("artifacts", []):
                path = Path(artifact["path"])
                actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
                if actual != artifact.get("sha256"):
                    problems.append({"unit": row["id"], "artifact": str(path), "expected": artifact.get("sha256"), "actual": actual})
                    db.execute("UPDATE work_units SET status='blocked',updated_at=? WHERE id=?", (now(), row["id"]))
                    event(db, "artifact.integrity_failed", row["id"], problems[-1])
        event(db, "workflow.reconciled", None, {"expired_leases": expired, "artifact_problems": len(problems)})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps({"expired_leases": expired, "artifact_problems": problems}, indent=2))


def cmd_status(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    if not db.execute("SELECT 1 FROM meta WHERE key='campaign_digest'").fetchone():
        raise SystemExit("workflow is not initialized")
    expire_leases(db)
    units = []
    for row in db.execute("SELECT id,status,attempts,lease_owner,lease_expires,result_json FROM work_units ORDER BY id").fetchall():
        units.append(dict(row))
    approvals = [dict(row) for row in db.execute("SELECT * FROM approvals ORDER BY id").fetchall()]
    meta = {row["key"]: row["value"] for row in db.execute("SELECT * FROM meta").fetchall()}
    counts = {status: db.execute("SELECT COUNT(*) AS n FROM work_units WHERE status=?", (status,)).fetchone()["n"] for status in ("pending", "leased", "succeeded", "failed", "blocked")}
    print(json.dumps({"meta": meta, "counts": counts, "work_units": units, "approvals": approvals}, indent=2, ensure_ascii=False))


def cmd_audit(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    problems = []
    # `blocked` units are included: reconcile moves an integrity-failed unit from
    # `succeeded` to `blocked`, and auditing only `succeeded` meant running reconcile
    # after a tamper made the top-line audit report the run clean.
    blocked = []
    for row in db.execute("SELECT id,status,result_json FROM work_units ORDER BY id").fetchall():
        if row["status"] == "blocked":
            blocked.append(row["id"])
        if row["status"] not in {"succeeded", "blocked"}:
            continue
        result = json.loads(row["result_json"] or "{}")
        for artifact in result.get("artifacts", []):
            path = Path(artifact["path"])
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            if actual != artifact.get("sha256"):
                problems.append({"unit": row["id"], "status": row["status"], "artifact": str(path),
                                 "actual": actual, "expected": artifact.get("sha256")})
    events = [dict(row) for row in db.execute("SELECT seq,at,type,unit_id,payload_json FROM events ORDER BY seq").fetchall()]
    event_digest = hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print(json.dumps({"valid": not problems and not blocked, "artifact_problems": problems,
                      "blocked_units": blocked, "event_count": len(events), "event_digest": event_digest}, indent=2))
    if problems or blocked:
        raise SystemExit(2)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("init"); q.add_argument("--campaign", required=True); q.add_argument("--db", required=True); q.add_argument("--force", action="store_true"); q.add_argument("--replace", action="store_true"); q.set_defaults(func=cmd_init)
    q = sub.add_parser("claim"); q.add_argument("--db", required=True); q.add_argument("--worker", required=True); q.add_argument("--lease-seconds", type=int, default=900); q.add_argument("--max-concurrency", type=int, default=4); q.set_defaults(func=cmd_claim)
    q = sub.add_parser("heartbeat"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--lease-seconds", type=int, default=900); q.set_defaults(func=cmd_heartbeat)
    q = sub.add_parser("complete"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--artifact", action="append", default=[]); q.add_argument("--acceptance-evidence", required=True); q.set_defaults(func=cmd_complete)
    q = sub.add_parser("fail"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--reason", required=True); q.add_argument("--retryable", action="store_true"); q.add_argument("--default-retry-limit", type=int, default=2); q.set_defaults(func=cmd_fail)
    q = sub.add_parser("approve"); q.add_argument("--db", required=True); q.add_argument("--approval", required=True); q.add_argument("--by", required=True); q.add_argument("--evidence", required=True); q.set_defaults(func=cmd_approve)
    q = sub.add_parser("stop"); q.add_argument("--db", required=True); q.add_argument("--reason", required=True); q.add_argument("--resume", action="store_true"); q.set_defaults(func=cmd_stop)
    q = sub.add_parser("reconcile"); q.add_argument("--db", required=True); q.set_defaults(func=cmd_reconcile)
    q = sub.add_parser("status"); q.add_argument("--db", required=True); q.set_defaults(func=cmd_status)
    q = sub.add_parser("audit"); q.add_argument("--db", required=True); q.set_defaults(func=cmd_audit)
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
