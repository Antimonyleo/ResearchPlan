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
import importlib.util
import json
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Any

VERSION = "0.9.0"
FINAL = {"succeeded", "failed", "blocked"}
EVENT_GENESIS = "sha256:" + ("0" * 64)


def load_rescamp_engine():
    """Load the sibling compiler without requiring an installed package."""
    path = Path(__file__).resolve().with_name("rescamp.py")
    spec = importlib.util.spec_from_file_location("rescamp_workflow_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load ResCamp validator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
      unit_id TEXT, payload_json TEXT NOT NULL,
      prev_hash TEXT NOT NULL DEFAULT '', event_hash TEXT NOT NULL DEFAULT '',
      state_hash TEXT NOT NULL DEFAULT ''
    );
    """)
    columns = {row["name"] for row in db.execute("PRAGMA table_info(events)").fetchall()}
    if "prev_hash" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN prev_hash TEXT NOT NULL DEFAULT ''")
    if "event_hash" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN event_hash TEXT NOT NULL DEFAULT ''")
    if "state_hash" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN state_hash TEXT NOT NULL DEFAULT ''")


def workflow_state_hash(db: sqlite3.Connection) -> str:
    projection = {
        "meta": {
            row["key"]: row["value"]
            for row in db.execute(
                "SELECT key,value FROM meta WHERE key NOT IN ('event_count','event_head') ORDER BY key"
            ).fetchall()
        },
        "approvals": [
            dict(row) for row in db.execute("SELECT * FROM approvals ORDER BY id").fetchall()
        ],
        "work_units": [
            dict(row) for row in db.execute("SELECT * FROM work_units ORDER BY id").fetchall()
        ],
    }
    encoded = json.dumps(
        projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def hash_event(seq: int, at: str, kind: str, unit_id: str | None,
               payload_json: str, previous: str, state_hash: str) -> str:
    record = {
        "seq": seq, "at": at, "type": kind, "unit_id": unit_id,
        "payload_json": payload_json, "prev_hash": previous,
        "state_hash": state_hash,
    }
    encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def event(db: sqlite3.Connection, kind: str, unit_id: str | None, payload: dict[str, Any]) -> None:
    at = now()
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    head = db.execute("SELECT value FROM meta WHERE key='event_head'").fetchone()
    previous = head["value"] if head else EVENT_GENESIS
    state_hash = workflow_state_hash(db)
    cursor = db.execute(
        "INSERT INTO events(at,type,unit_id,payload_json,prev_hash,event_hash,state_hash) "
        "VALUES(?,?,?,?,?,'',?)",
        (at, kind, unit_id, payload_json, previous, state_hash),
    )
    seq = int(cursor.lastrowid)
    digest = hash_event(seq, at, kind, unit_id, payload_json, previous, state_hash)
    db.execute("UPDATE events SET event_hash=? WHERE seq=?", (digest, seq))
    count = db.execute("SELECT value FROM meta WHERE key='event_count'").fetchone()
    next_count = (int(count["value"]) if count else 0) + 1
    db.execute("INSERT INTO meta(key,value) VALUES('event_head',?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (digest,))
    db.execute("INSERT INTO meta(key,value) VALUES('event_count',?) "
               "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(next_count),))


def read_campaign(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("campaign", data)


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return dt.datetime.fromisoformat(normalized)


def aware_time(value: Any, label: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{label} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = parse_time(value)
    except ValueError:
        raise SystemExit(f"{label} must be a valid ISO-8601 timestamp") from None
    if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit(f"{label} must include a timezone")
    return parsed


def nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SystemExit(f"{label} must be a non-negative integer")
    return value


def positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise SystemExit(f"{label} must be a positive integer")
    return value


def declared_approvals(campaign: dict[str, Any]) -> dict[str, dict[str, Any]]:
    resources = campaign.get("resources_dispatch", {})
    ethics = campaign.get("ethics_rights_safety", {})
    resource_records = resources.get("approvals", [])
    human_records = ethics.get("human_approval_points", [])
    if not isinstance(resource_records, list) or not isinstance(human_records, list):
        raise SystemExit("approval declarations must be lists of structured objects")
    records = resource_records + human_records
    declared: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not str(record.get("id", "")).strip():
            raise SystemExit(
                "runtime approvals must be structured objects with non-empty IDs; "
                f"approval record {index} is not dispatchable"
            )
        ident = str(record["id"])
        if ident in declared:
            raise SystemExit(f"duplicate declared approval ID {ident!r}")
        declared[ident] = record
    return declared


def validate_dispatch_contract(campaign: dict[str, Any]) -> tuple[int, dict[str, dict[str, Any]]]:
    resources = campaign.get("resources_dispatch", {})
    concurrency = positive_int(resources.get("max_concurrency"),
                               "campaign.resources_dispatch.max_concurrency")
    declared = declared_approvals(campaign)

    actions: dict[str, dict[str, Any]] = {}
    for index, action in enumerate(campaign.get("ethics_rights_safety", {}).get("external_actions", [])):
        if not isinstance(action, dict) or not str(action.get("id", "")).strip():
            raise SystemExit(f"external action {index} must have a non-empty ID")
        ident = str(action["id"])
        if ident in actions:
            raise SystemExit(f"duplicate external action ID {ident!r}")
        approval = action.get("approval_id")
        if approval not in declared:
            raise SystemExit(f"external action {ident!r} references unknown approval {approval!r}")
        actions[ident] = action

    for unit in campaign.get("work_units", []):
        ident = unit.get("id", "")
        approval_ids = unit.get("approval_ids", [])
        external_action_ids = unit.get("external_action_ids", [])
        if not isinstance(approval_ids, list) or any(not isinstance(item, str) or not item for item in approval_ids):
            raise SystemExit(f"work unit {ident!r} approval_ids must be a list of non-empty strings")
        if len(approval_ids) != len(set(approval_ids)):
            raise SystemExit(f"work unit {ident!r} has duplicate approval IDs")
        unknown_approvals = sorted(set(approval_ids) - set(declared))
        if unknown_approvals:
            raise SystemExit(f"work unit {ident!r} references unknown approvals: {unknown_approvals}")
        if not isinstance(external_action_ids, list) or any(
                not isinstance(item, str) or not item for item in external_action_ids):
            raise SystemExit(f"work unit {ident!r} external_action_ids must be a list of non-empty strings")
        unknown_actions = sorted(set(external_action_ids) - set(actions))
        if unknown_actions:
            raise SystemExit(f"work unit {ident!r} references unknown external actions: {unknown_actions}")
        required = {str(actions[item]["approval_id"]) for item in external_action_ids}
        missing = sorted(required - set(approval_ids))
        if missing:
            raise SystemExit(
                f"work unit {ident!r} does not bind approvals required by its external actions: {missing}"
            )
        nonnegative_int(unit.get("retry_limit"), f"work unit {ident!r} retry_limit")
        if unit.get("deadline_at") is not None:
            aware_time(unit["deadline_at"], f"work unit {ident!r} deadline_at")
    return concurrency, declared


def artifact_problems(result: dict[str, Any]) -> list[dict[str, Any]]:
    problems = []
    if not isinstance(result, dict):
        return [{"artifact": None, "expected": "structured result record", "actual": type(result).__name__}]
    artifacts = result.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        return [{"artifact": None, "expected": "at least one recorded artifact", "actual": None}]
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            problems.append({
                "artifact": None, "expected": f"structured artifact record at index {index}",
                "actual": type(artifact).__name__,
            })
            continue
        path = Path(artifact.get("path", ""))
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != artifact.get("sha256"):
            problems.append({"artifact": str(path), "expected": artifact.get("sha256"), "actual": actual})
    return problems


def expire_leases(db: sqlite3.Connection) -> int:
    rows = db.execute("SELECT id,lease_expires,attempts,spec_json FROM work_units WHERE status='leased'").fetchall()
    current = dt.datetime.now(dt.timezone.utc)
    expired = [row for row in rows if parse_time(row["lease_expires"]) and parse_time(row["lease_expires"]) <= current]
    for row in expired:
        spec = json.loads(row["spec_json"])
        limit = nonnegative_int(spec.get("retry_limit"), f"work unit {row['id']!r} retry_limit")
        retry = row["attempts"] <= limit
        status = "pending" if retry else "failed"
        result = {
            "failed_at": now(), "reason": "lease expired", "retryable": retry,
            "requeued": retry, "attempts": row["attempts"], "retry_limit": limit,
        }
        db.execute(
            "UPDATE work_units SET status=?,lease_token=NULL,lease_owner=NULL,lease_expires=NULL,"
            "result_json=?,updated_at=? WHERE id=?",
            (status, json.dumps(result, sort_keys=True), now(), row["id"]),
        )
        event(db, "lease.expired", row["id"], result)
    return len(expired)


def unit_ready(db: sqlite3.Connection, spec: dict[str, Any]) -> tuple[bool, str]:
    dependencies = spec.get("dependency_ids", [])
    for dep in dependencies:
        row = db.execute("SELECT status,result_json FROM work_units WHERE id=?", (dep,)).fetchone()
        if row is None:
            return False, f"unknown dependency {dep}"
        if row["status"] != "succeeded":
            return False, f"dependency {dep} is {row['status']}"
        problems = artifact_problems(json.loads(row["result_json"] or "{}"))
        if problems:
            db.execute("UPDATE work_units SET status='blocked',updated_at=? WHERE id=?", (now(), dep))
            for problem in problems:
                payload = {"dependency_of": spec.get("id"), **problem}
                event(db, "artifact.integrity_failed", dep, payload)
            return False, f"dependency {dep} artifact integrity failed"
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
    validation = load_rescamp_engine().validate_state(source, include_reviews=True)
    if not validation.get("execution_ready"):
        codes = ", ".join(item.get("code", "invalid") for item in validation.get("errors", []))
        raise SystemExit(
            "campaign failed dispatch validation" + (f": {codes}" if codes else "") + ".\n"
            "Finalize a current, reviewed campaign before initializing the queue."
        )
    # Status remains a useful assertion from rendering, but is never trusted in place
    # of revalidation. --force permits a reviewed dry-run whose runtime/status flags are
    # deliberately disabled; it does not bypass design or review validation.
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
    max_concurrency, approvals = validate_dispatch_contract(campaign)
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
            "campaign_content_digest": validation["content_digest"],
            "campaign_path": str(campaign_path),
            "max_concurrency": str(max_concurrency),
            "enforced_limits": json.dumps(
                ["dependency_artifact_integrity", "retry_limit", "lease_expiry", "deadline_at", "max_concurrency"],
                separators=(",", ":"),
            ),
            "attested_limits": json.dumps(
                ["resource_ceiling", "cost", "tool_use"], separators=(",", ":")
            ),
            "stopped": "false",
            "created_at": now(),
        }
        for key, value in meta.items():
            db.execute("INSERT INTO meta(key,value) VALUES(?,?)", (key, value))
        for unit in units:
            db.execute("INSERT INTO work_units(id,spec_json,status,updated_at) VALUES(?,?,?,?)",
                       (unit["id"], json.dumps(unit, sort_keys=True, ensure_ascii=False), "pending", now()))
        for approval in sorted(approvals):
            db.execute("INSERT INTO approvals(id,status,updated_at) VALUES(?,?,?)", (approval, "pending", now()))
        event(db, "workflow.initialized", None, {"campaign_digest": digest, "work_units": ids, "forced": bool(args.force)})
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    print(json.dumps({
        "db": str(Path(args.db).resolve()), "campaign_digest": digest,
        "work_units": len(units), "max_concurrency": max_concurrency,
        "enforced_limits": ["dependency_artifact_integrity", "retry_limit", "lease_expiry", "deadline_at", "max_concurrency"],
        "attested_limits": ["resource_ceiling", "cost", "tool_use"],
    }, indent=2))


def cmd_claim(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        require_valid_event_chain(db)
        expire_leases(db)
        stopped = db.execute("SELECT value FROM meta WHERE key='stopped'").fetchone()
        if stopped is None:
            raise SystemExit("workflow is not initialized")
        if stopped["value"] == "true":
            raise SystemExit("workflow is stopped")
        active = db.execute("SELECT COUNT(*) AS n FROM work_units WHERE status='leased'").fetchone()["n"]
        ceiling_row = db.execute("SELECT value FROM meta WHERE key='max_concurrency'").fetchone()
        if ceiling_row is None:
            raise SystemExit("workflow has no declared concurrency ceiling; reinitialize it")
        campaign_ceiling = positive_int(int(ceiling_row["value"]), "campaign max_concurrency")
        requested = getattr(args, "max_concurrency", None)
        if requested is not None:
            requested = positive_int(requested, "--max-concurrency")
            if requested > campaign_ceiling:
                raise SystemExit(
                    f"--max-concurrency cannot raise campaign ceiling {campaign_ceiling}; "
                    "omit it or provide a lower value"
                )
        max_concurrency = requested or campaign_ceiling
        if active >= max_concurrency:
            raise SystemExit("concurrency ceiling reached")
        chosen = None
        blocked_reasons = []
        for row in db.execute("SELECT * FROM work_units WHERE status='pending' ORDER BY id").fetchall():
            spec = json.loads(row["spec_json"])
            deadline = aware_time(spec["deadline_at"], f"work unit {row['id']!r} deadline_at") \
                if spec.get("deadline_at") is not None else None
            if deadline is not None and deadline <= dt.datetime.now(dt.timezone.utc):
                db.execute("UPDATE work_units SET status='failed',updated_at=? WHERE id=?", (now(), row["id"]))
                event(db, "work.deadline_exceeded", row["id"], {"deadline_at": deadline.isoformat()})
                blocked_reasons.append({"id": row["id"], "reason": "deadline exceeded"})
                continue
            retry_limit = nonnegative_int(spec.get("retry_limit"), f"work unit {row['id']!r} retry_limit")
            if row["attempts"] >= retry_limit + 1:
                db.execute("UPDATE work_units SET status='failed',updated_at=? WHERE id=?", (now(), row["id"]))
                event(db, "work.retry_exhausted", row["id"], {
                    "attempts": row["attempts"], "retry_limit": retry_limit,
                })
                blocked_reasons.append({"id": row["id"], "reason": "retry limit exhausted"})
                continue
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
        if args.lease_seconds <= 0:
            raise SystemExit("--lease-seconds must be positive")
        token = secrets.token_urlsafe(24)
        expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=args.lease_seconds)
        if deadline is not None:
            expiry = min(expiry, deadline)
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
    spec = json.loads(row["spec_json"])
    if spec.get("deadline_at") is not None:
        deadline = aware_time(spec["deadline_at"], f"work unit {ident!r} deadline_at")
        if deadline <= dt.datetime.now(dt.timezone.utc):
            raise SystemExit("work-unit deadline exceeded")
    return row


def cmd_heartbeat(args: argparse.Namespace) -> None:
    if args.lease_seconds <= 0:
        raise SystemExit("--lease-seconds must be positive")
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        require_valid_event_chain(db)
        leased_row(db, args.unit, args.token)
        expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=args.lease_seconds)
        row = db.execute("SELECT spec_json FROM work_units WHERE id=?", (args.unit,)).fetchone()
        spec = json.loads(row["spec_json"])
        if spec.get("deadline_at") is not None:
            expiry = min(expiry, aware_time(spec["deadline_at"], f"work unit {args.unit!r} deadline_at"))
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
        require_valid_event_chain(db)
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
        require_valid_event_chain(db)
        row = leased_row(db, args.unit, args.token)
        spec = json.loads(row["spec_json"])
        limit = nonnegative_int(spec.get("retry_limit"), f"work unit {args.unit!r} retry_limit")
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
    if not args.by.strip() or not args.evidence.strip():
        raise SystemExit("approval identity and evidence must be non-empty")
    db = connect(Path(args.db).resolve())
    schema(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        require_valid_event_chain(db)
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
        require_valid_event_chain(db)
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
        require_valid_event_chain(db)
        expired = expire_leases(db)
        for row in db.execute("SELECT id,result_json FROM work_units WHERE status IN ('succeeded','blocked')").fetchall():
            result = json.loads(row["result_json"] or "{}")
            for problem in artifact_problems(result):
                problem = {"unit": row["id"], **problem}
                problems.append(problem)
                db.execute("UPDATE work_units SET status='blocked',updated_at=? WHERE id=?", (now(), row["id"]))
                event(db, "artifact.integrity_failed", row["id"], problem)
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
    db.execute("BEGIN IMMEDIATE")
    try:
        require_valid_event_chain(db)
        expire_leases(db)
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    units = []
    for row in db.execute("SELECT id,status,attempts,lease_owner,lease_expires,result_json FROM work_units ORDER BY id").fetchall():
        units.append(dict(row))
    approvals = [dict(row) for row in db.execute("SELECT * FROM approvals ORDER BY id").fetchall()]
    meta = {row["key"]: row["value"] for row in db.execute("SELECT * FROM meta").fetchall()}
    counts = {status: db.execute("SELECT COUNT(*) AS n FROM work_units WHERE status=?", (status,)).fetchone()["n"] for status in ("pending", "leased", "succeeded", "failed", "blocked")}
    print(json.dumps({"meta": meta, "counts": counts, "work_units": units, "approvals": approvals}, indent=2, ensure_ascii=False))


def event_chain_problems(db: sqlite3.Connection) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    rows = db.execute(
        "SELECT seq,at,type,unit_id,payload_json,prev_hash,event_hash,state_hash "
        "FROM events ORDER BY seq"
    ).fetchall()
    count_row = db.execute("SELECT value FROM meta WHERE key='event_count'").fetchone()
    head_row = db.execute("SELECT value FROM meta WHERE key='event_head'").fetchone()
    if count_row is None or head_row is None:
        return [{"code": "event.anchor_missing"}]
    try:
        anchored_count = int(count_row["value"])
    except ValueError:
        return [{"code": "event.count_invalid", "actual": count_row["value"]}]
    if anchored_count != len(rows):
        problems.append({"code": "event.count_mismatch", "expected": anchored_count, "actual": len(rows)})
    previous = EVENT_GENESIS
    for row in rows:
        if row["prev_hash"] != previous:
            problems.append({
                "code": "event.previous_hash_mismatch", "seq": row["seq"],
                "expected": previous, "actual": row["prev_hash"],
            })
        expected = hash_event(
            row["seq"], row["at"], row["type"], row["unit_id"],
            row["payload_json"], row["prev_hash"], row["state_hash"],
        )
        if row["event_hash"] != expected:
            problems.append({
                "code": "event.hash_mismatch", "seq": row["seq"],
                "expected": expected, "actual": row["event_hash"],
            })
        previous = row["event_hash"]
    if not rows:
        problems.append({"code": "event.history_empty"})
    else:
        current_state_hash = workflow_state_hash(db)
        if rows[-1]["state_hash"] != current_state_hash:
            problems.append({
                "code": "event.state_mismatch",
                "expected": rows[-1]["state_hash"], "actual": current_state_hash,
            })
    if head_row["value"] != previous:
        problems.append({
            "code": "event.head_mismatch", "expected": head_row["value"], "actual": previous,
        })
    return problems


def require_valid_event_chain(db: sqlite3.Connection) -> None:
    if not db.execute("SELECT 1 FROM meta WHERE key='campaign_digest'").fetchone():
        raise SystemExit("workflow is not initialized")
    problems = event_chain_problems(db)
    if problems:
        codes = ", ".join(problem["code"] for problem in problems)
        raise SystemExit(
            f"workflow event history is corrupt ({codes}); run audit for details or "
            "reinitialize with init --replace"
        )


def cmd_audit(args: argparse.Namespace) -> None:
    db = connect(Path(args.db).resolve())
    schema(db)
    digest_row = db.execute("SELECT value FROM meta WHERE key='campaign_digest'").fetchone()
    if digest_row is None:
        raise SystemExit("workflow is not initialized")
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
        for problem in artifact_problems(result):
            problems.append({"unit": row["id"], "status": row["status"], **problem})
    chain_problems = event_chain_problems(db)
    events = [dict(row) for row in db.execute(
        "SELECT seq,at,type,unit_id,payload_json,prev_hash,event_hash,state_hash "
        "FROM events ORDER BY seq"
    ).fetchall()]
    event_digest = hashlib.sha256(json.dumps(events, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print(json.dumps({"valid": not problems and not blocked and not chain_problems, "artifact_problems": problems,
                      "blocked_units": blocked, "event_count": len(events), "event_digest": event_digest,
                      "event_chain_problems": chain_problems}, indent=2))
    if problems or blocked or chain_problems:
        raise SystemExit(2)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("init"); q.add_argument("--campaign", required=True); q.add_argument("--db", required=True); q.add_argument("--force", action="store_true"); q.add_argument("--replace", action="store_true"); q.set_defaults(func=cmd_init)
    q = sub.add_parser("claim"); q.add_argument("--db", required=True); q.add_argument("--worker", required=True); q.add_argument("--lease-seconds", type=int, default=900); q.add_argument("--max-concurrency", type=int); q.set_defaults(func=cmd_claim)
    q = sub.add_parser("heartbeat"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--lease-seconds", type=int, default=900); q.set_defaults(func=cmd_heartbeat)
    q = sub.add_parser("complete"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--artifact", action="append", default=[]); q.add_argument("--acceptance-evidence", required=True); q.set_defaults(func=cmd_complete)
    q = sub.add_parser("fail"); q.add_argument("--db", required=True); q.add_argument("--unit", required=True); q.add_argument("--token", required=True); q.add_argument("--reason", required=True); q.add_argument("--retryable", action="store_true"); q.set_defaults(func=cmd_fail)
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
