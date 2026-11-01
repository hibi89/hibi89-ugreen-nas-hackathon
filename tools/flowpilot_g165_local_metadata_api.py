"""G165: explicit two-phase owner-local read-only metadata review.

Server is loopback-only. Root is selected at process launch, never via HTTP.
No root is inspected during preview; approval is exact, expiring, single-use.
All output is redacted metadata indexes/states. NOT NAS/Uliya, no file reads.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import secrets
import threading
import time

from flowpilot_owner_local_audit import inspect_owner_folder, OwnerAuditError, _valid_relative

SCHEMA = "flowpilot-owner-local-metadata-session-v1"
MAX_REVIEWS = 32
MAX_PATHS = 20
EXPIRY_SECONDS = 600


class MetadataRefused(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


class MetadataGate:
    """In-memory grant. Never persist a path or consent token into SQLite."""

    def __init__(self, root: Path | None):
        self._root = None
        if root is not None:
            if (not isinstance(root, Path) or not root.is_absolute()
                    or len(str(root)) > 2048 or str(root).startswith(("\\\\", "//"))):
                raise MetadataRefused("INVALID_LOCAL_ROOT_CONFIGURATION", 400)
            # Do NOT call stat, lstat, exists or resolve on root until approved.
            self._root = root
        self._lock = threading.RLock()
        self._reviews: dict[str, dict] = {}

    def _prune(self):
        now = time.monotonic()
        for token in list(self._reviews):
            if now - self._reviews[token]["created"] > EXPIRY_SECONDS:
                del self._reviews[token]

    @staticmethod
    def _public(token: str, item: dict) -> dict:
        return {
            "schema": SCHEMA, "review_id": token, "status": item["status"],
            "scope_sha256": item["digest"], "required_count": len(item["required"]),
            "approved_local_metadata_access": item["status"] in
                ("LOCAL_METADATA_FINDINGS_READY", "LOCAL_METADATA_BLOCKED"),
            "inspection_result": item["result"],
            "owner_root_returned": False, "raw_filenames_returned": False,
            "file_contents_opened": False, "nas_verified": False,
            "registered_expert_invoked": False, "release_gate": "HOLD",
        }

    def begin(self, goal: object, required: object) -> dict:
        with self._lock:
            self._prune()
            if self._root is None:
                raise MetadataRefused("LOCAL_ROOT_NOT_CONFIGURED", 409)
            # First version supports exactly one proven local metadata action.
            if type(goal) is not str or goal != "check required files":
                raise MetadataRefused("UNSUPPORTED_METADATA_GOAL", 422)
            if type(required) is not list or not 1 <= len(required) <= MAX_PATHS:
                raise MetadataRefused("INVALID_METADATA_CHECKLIST", 400)
            try:
                items = tuple(_valid_relative(p) for p in required)
            except (OwnerAuditError, TypeError, ValueError) as exc:
                raise MetadataRefused("INVALID_METADATA_CHECKLIST", 400) from exc
            if len(set(items)) != len(items):
                raise MetadataRefused("DUPLICATE_METADATA_CHECKLIST", 400)
            try:
                preflight = inspect_owner_folder(self._root, list(items), goal=goal,
                                                 metadata_consent=False)
            except (OwnerAuditError, OSError, TypeError, ValueError) as exc:
                raise MetadataRefused("METADATA_PREFLIGHT_REFUSED", 400) from exc
            if (preflight.get("status") != "WAITING_APPROVAL"
                    or preflight.get("inspected_local_metadata") is not False):
                raise MetadataRefused("METADATA_PREFLIGHT_UNEXPECTED")
            if len(self._reviews) >= MAX_REVIEWS:
                raise MetadataRefused("REVIEW_CAPACITY_REACHED", 429)
            token = "rev_" + secrets.token_hex(16)
            nonce = secrets.token_hex(16)
            # Salt prevents easy guesses of private required relative filenames.
            raw = json.dumps({"goal": goal, "required": items, "root": str(self._root),
                              "nonce": nonce}, ensure_ascii=True,
                             sort_keys=True, separators=(",", ":")).encode("ascii")
            digest = sha256(raw).hexdigest()
            item = {"created": time.monotonic(), "goal": goal, "required": items,
                    "digest": digest, "status": "WAITING_APPROVAL", "result": None}
            self._reviews[token] = item
            return self._public(token, item)

    def _lookup(self, token: str):
        self._prune()
        if (type(token) is not str or not token.startswith("rev_")
                or len(token) != 36 or
                any(c not in "0123456789abcdef" for c in token[4:])):
            raise MetadataRefused("INVALID_REVIEW_ID", 400)
        item = self._reviews.get(token)
        if item is None:
            raise MetadataRefused("REVIEW_NOT_FOUND_OR_EXPIRED", 404)
        return item

    def get(self, token: str) -> dict:
        with self._lock:
            return self._public(token, self._lookup(token))

    def cancel(self, token: str) -> dict:
        with self._lock:
            item = self._lookup(token)
            if item["status"] != "WAITING_APPROVAL":
                raise MetadataRefused("REVIEW_ALREADY_CONSUMED")
            item["status"] = "CANCELED"
            item["required"] = tuple()  # no need to retain unapproved filenames
            return self._public(token, item)

    def approve(self, token: str, digest: str, acknowledgement: str) -> dict:
        with self._lock:
            item = self._lookup(token)
            if item["status"] != "WAITING_APPROVAL":
                raise MetadataRefused("REVIEW_ALREADY_CONSUMED")
            if (type(digest) is not str or digest != item["digest"]
                    or type(acknowledgement) is not str
                    or acknowledgement != "APPROVE_LOCAL_METADATA_READ_ONLY"):
                raise MetadataRefused("EXACT_LOCAL_METADATA_APPROVAL_REQUIRED", 403)
            # Consume before any real metadata operation; failure is not retried.
            item["status"] = "INSPECTION_STARTED"
            try:
                outcome = inspect_owner_folder(
                    self._root, list(item["required"]),
                    goal=item["goal"], metadata_consent=True)
                if (outcome.get("file_contents_opened") is not False
                        or outcome.get("raw_paths_or_file_names_in_output") is not False
                        or outcome.get("inspected_local_metadata") is not True):
                    raise MetadataRefused("UNSAFE_METADATA_ADAPTER_RESULT")
                states = outcome.get("items")
                if (type(states) is not list or len(states) != len(item["required"])
                        or any(type(x) is not dict or
                               x.get("state") not in
                               ("PRESENT", "MISSING", "NOT_CHECKED", "VERSION_REVIEW")
                               for x in states)):
                    raise MetadataRefused("INVALID_METADATA_FINDINGS")
                result = [{"index": idx+1, "state": row["state"]}
                          for idx, row in enumerate(states)]
                item["status"] = ("LOCAL_METADATA_FINDINGS_READY"
                                  if all(x["state"] == "PRESENT" for x in result)
                                  else "LOCAL_METADATA_BLOCKED")
                item["result"] = result
            except (OwnerAuditError, OSError, TypeError, ValueError, MetadataRefused):
                item["status"] = "INSPECTION_REFUSED"
                item["result"] = None
            finally:
                item["required"] = tuple()  # discard file names, keep count separately
            return self._public(token, item)
