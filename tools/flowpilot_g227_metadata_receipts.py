"""G227: persist ONLY redacted, owner-approved local metadata evidence.

This is a local filesystem lstat receipt, NOT verified NAS/registered Expert
evidence. No raw paths, filenames, file contents, tokens or customer bytes are
stored in this table. SQLite hashes are integrity hints, not notarization.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3

SCHEMA = "flowpilot-g227-redacted-metadata-evidence-v1"
ACK = "SAVE_REDACTED_LOCAL_METADATA_RECEIPT"
STATUS = frozenset(("LOCAL_METADATA_FINDINGS_READY", "LOCAL_METADATA_BLOCKED"))
STATES = frozenset(("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW"))
TABLE = "fp_backend_local_metadata_evidence"
WF = re.compile(r"wf_[0-9a-f]{32}\Z")
REVIEW = re.compile(r"rev_[0-9a-f]{32}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


class MetadataReceiptRefused(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


def _serialize(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _sha(payload: dict) -> str:
    return hashlib.sha256(_serialize(payload).encode("ascii")).hexdigest()


def _validate(payload: object) -> dict:
    if type(payload) is not dict or set(payload) != {
        "schema", "workflow_id", "scope_sha256", "inspection_status",
        "item_count", "findings", "local_metadata_only", "file_contents_opened",
        "registered_expert_invoked", "nas_verified", "release_gate",
    }:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_SHAPE_INVALID")
    if (payload["schema"] != SCHEMA or
            type(payload["workflow_id"]) is not str or
            WF.fullmatch(payload["workflow_id"]) is None or
            type(payload["scope_sha256"]) is not str or
            HASH.fullmatch(payload["scope_sha256"]) is None or
            payload["inspection_status"] not in STATUS or
            type(payload["item_count"]) is not int or
            not 1 <= payload["item_count"] <= 20 or
            payload["local_metadata_only"] is not True or
            payload["file_contents_opened"] is not False or
            payload["registered_expert_invoked"] is not False or
            payload["nas_verified"] is not False or
            payload["release_gate"] != "HOLD"):
        raise MetadataReceiptRefused("METADATA_EVIDENCE_VALUES_INVALID")
    rows = payload["findings"]
    if (type(rows) is not list or len(rows) != payload["item_count"] or
            any(type(x) is not dict or set(x) != {"index", "state"} or
                type(x["index"]) is not int or x["index"] != i or
                type(x["state"]) is not str or x["state"] not in STATES
                for i, x in enumerate(rows, 1))):
        raise MetadataReceiptRefused("METADATA_EVIDENCE_FINDINGS_INVALID")
    all_present = all(row["state"] == "PRESENT" for row in rows)
    if all_present != (payload["inspection_status"] == "LOCAL_METADATA_FINDINGS_READY"):
        raise MetadataReceiptRefused("METADATA_EVIDENCE_STATUS_CONFLICT")
    if len(_serialize(payload)) > 8192:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_OVERSIZED")
    return payload


def from_completed_review(workflow_id: object, scope: object, review: object) -> dict:
    """Validate an already-approved in-memory MetadataGate result.

    Never store the actual review ID in the public result, or owner paths.
    Approval to read must already have happened; saving needs a separate ACK.
    """
    if (type(workflow_id) is not str or WF.fullmatch(workflow_id) is None or
            type(scope) is not str or HASH.fullmatch(scope) is None or
            type(review) is not dict or review.get("scope_sha256") != scope or
            review.get("status") not in STATUS or
            review.get("approved_local_metadata_access") is not True or
            review.get("file_contents_opened") is not False or
            review.get("raw_filenames_returned") is not False or
            review.get("nas_verified") is not False or
            review.get("registered_expert_invoked") is not False):
        raise MetadataReceiptRefused("COMPLETED_LOCAL_REVIEW_REQUIRED", 403)
    result = review.get("inspection_result")
    if type(result) is not list or type(review.get("required_count")) is not int:
        raise MetadataReceiptRefused("INVALID_LOCAL_REVIEW")
    # Reconstruct from exact allowed keys, discarding all other data.
    payload = {
        "schema": SCHEMA, "workflow_id": workflow_id, "scope_sha256": scope,
        "inspection_status": review["status"],
        "item_count": review["required_count"],
        "findings": [{"index": x.get("index"), "state": x.get("state")}
                     if type(x) is dict else {} for x in result],
        "local_metadata_only": True, "file_contents_opened": False,
        "registered_expert_invoked": False, "nas_verified": False,
        "release_gate": "HOLD",
    }
    return _validate(payload)


def _read(db: sqlite3.Connection, workflow_id: str) -> dict:
    if type(workflow_id) is not str or WF.fullmatch(workflow_id) is None:
        raise MetadataReceiptRefused("WORKFLOW_ID_INVALID", 400)
    table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE,)
    ).fetchone()
    if table is None:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_NOT_FOUND", 404)
    row = db.execute(
        "SELECT payload_json,payload_sha FROM fp_backend_local_metadata_evidence "
        "WHERE workflow_id=?", (workflow_id,)
    ).fetchone()
    if row is None:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_NOT_FOUND", 404)
    raw, digest = row
    if type(raw) is not str or len(raw) > 8192 or type(digest) is not str:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_CORRUPT")
    try:
        def unique(pairs):
            result = {}
            for k, v in pairs:
                if k in result:
                    raise ValueError("DUPLICATE_FIELD")
                result[k] = v
            return result
        payload = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError, TypeError, RecursionError) as exc:
        raise MetadataReceiptRefused("METADATA_EVIDENCE_CORRUPT") from exc
    _validate(payload)
    if (payload["workflow_id"] != workflow_id or digest != _sha(payload) or
            raw != _serialize(payload)):
        raise MetadataReceiptRefused("METADATA_EVIDENCE_HASH_MISMATCH")
    return {
        "schema": SCHEMA, "status": "REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS",
        "record_sha256": digest, "record": payload, "owner_paths_stored": False,
        "source_files_opened": False, "verified_actual_nas": False,
        "independently_notarized": False, "release_gate": "HOLD",
    }


def read_receipt(db: sqlite3.Connection, workflow_id: str) -> dict:
    return _read(db, workflow_id)


def save_receipt(db: sqlite3.Connection, review_id: object,
                 payload: dict) -> dict:
    if (type(review_id) is not str or REVIEW.fullmatch(review_id) is None or
            not isinstance(db, sqlite3.Connection) or db.in_transaction):
        raise MetadataReceiptRefused("INVALID_RECEIPT_INPUT", 400)
    payload = _validate(payload)
    wf_id = payload["workflow_id"]
    raw, digest = _serialize(payload), _sha(payload)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute(
            "CREATE TABLE IF NOT EXISTS fp_backend_local_metadata_evidence ("
            "workflow_id TEXT PRIMARY KEY, review_id TEXT NOT NULL UNIQUE, "
            "payload_json TEXT NOT NULL, payload_sha TEXT NOT NULL)"
        )
        existing = db.execute(
            "SELECT review_id,payload_json,payload_sha FROM "
            "fp_backend_local_metadata_evidence WHERE workflow_id=?",
            (wf_id,)
        ).fetchone()
        if existing is not None:
            if existing != (review_id, raw, digest):
                raise MetadataReceiptRefused("METADATA_WORKFLOW_ALREADY_LINKED")
            # Exact identical second request is idempotent, not another scan.
        elif db.execute(
            "SELECT workflow_id FROM fp_backend_local_metadata_evidence "
            "WHERE review_id=?", (review_id,)
        ).fetchone() is not None:
            raise MetadataReceiptRefused("METADATA_REVIEW_ALREADY_LINKED")
        else:
            db.execute(
                "INSERT INTO fp_backend_local_metadata_evidence VALUES (?,?,?,?)",
                (wf_id, review_id, raw, digest),
            )
        db.commit()
        return _read(db, wf_id)
    except BaseException:
        db.rollback()
        raise
