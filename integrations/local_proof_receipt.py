"""Validate a user-provided local synthetic E2E report without overstating proof.

Only a strictly bounded, allowlisted subset of the report may be published.
A transcript/JSON supplied by an owner is NOT an independently replayed
test log and can NEVER establish Uliya registration, NAS access or release.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

EXPECTED_HAE_SHA = "9cba6424dadf3fadb0ccd6ed10040e322c4a62fa"
EXPECTED_SOVIA_SHA = "7418b23aff9b3abbd3faf5d1477e7244ec82b681"
EXPECTED_PROOF_TYPE = "REAL_HAE_LA_AND_SOVIA_SYNTHETIC_LOCAL_ONLY"

# Explicit allowlist: reject unexpected fields instead of persisting paths,
# opaque extra metadata, private source, or an unbounded reporter payload.
FIELDS = frozenset({
    "result", "proof_type", "hae_la_commit", "sovia_commit",
    "la_runtime_sha256", "sovia_preflight_sha256",
    "real_la_synthetic_sqlite", "real_la_approved_write_rows",
    "real_la_replay_duplicate_writes", "real_la_approval_receipts",
    "real_sovia_advisory", "scenario_count", "write_advisory_findings",
    "customer_data_used", "actual_nas_verified",
    "registered_uliya_expert_invoked", "devpost_submitted", "release_gate",
})
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ReceiptRejected(ValueError):
    """A local proof report is malformed, unsupported, or unsafe to publish."""


def validate_owner_reported_local_proof(report: Mapping[str, Any]) -> dict[str, Any]:
    """Return a redacted classification, not a claim of independent witnessing.

    The function does not contact GitHub or NAS, nor does it access local
    checkouts or call HAE/SOVIA itself. Its input is treated as untrusted.
    """
    if type(report) is not dict or set(report) != FIELDS:
        raise ReceiptRejected("UNEXPECTED_REPORT_FIELDS")
    for key, value in (
        ("result", "PASS"),
        ("proof_type", EXPECTED_PROOF_TYPE),
        ("hae_la_commit", EXPECTED_HAE_SHA),
        ("sovia_commit", EXPECTED_SOVIA_SHA),
        ("real_la_synthetic_sqlite", "PASS"),
        ("real_sovia_advisory", "PASS"),
        ("release_gate", "HOLD"),
    ):
        if type(report[key]) is not str or report[key] != value:
            raise ReceiptRejected("INVALID_" + key.upper())
    for name in ("la_runtime_sha256", "sovia_preflight_sha256"):
        if type(report[name]) is not str or not HEX64.fullmatch(report[name]):
            raise ReceiptRejected("INVALID_SOURCE_DIGEST")
    expected_counts = {
        "real_la_approved_write_rows": 1,
        "real_la_replay_duplicate_writes": 0,
        "real_la_approval_receipts": 1,
        "scenario_count": 4,
        "write_advisory_findings": 1,
    }
    for name, value in expected_counts.items():
        if type(report[name]) is not int or report[name] != value:
            raise ReceiptRejected("INVALID_SYNTHETIC_COUNT")
    for name in ("customer_data_used", "actual_nas_verified",
                 "registered_uliya_expert_invoked", "devpost_submitted"):
        if report[name] is not False:
            raise ReceiptRejected("UNVERIFIED_EXTERNAL_ACTION")

    # Hashes are reported by the owner command. They are not independently
    # measured by this parser, and no checksum trust is inferred.
    return {
        "result": "ACCEPTED_OWNER_REPORTED_SYNTHETIC_PROOF",
        "provenance": "USER_SUPPLIED_LOCAL_COMMAND_STDOUT",
        "independently_replayed_in_ugreen_ci": False,
        "hae_la_commit": EXPECTED_HAE_SHA,
        "sovia_commit": EXPECTED_SOVIA_SHA,
        "reported_la_runtime_sha256": report["la_runtime_sha256"],
        "reported_sovia_preflight_sha256": report["sovia_preflight_sha256"],
        "reported_actual_la_sqlite": "PASS",
        "reported_actual_sovia_advisory": "PASS",
        "synthetic_scenario_count": 4,
        "approved_synthetic_write_rows": 1,
        "approved_receipts": 1,
        "duplicate_write_rows": 0,
        "actual_nas_verified": False,
        "registered_uliya_expert_invoked": False,
        "customer_data_used": False,
        "official_creator_execution_verified": False,
        "devpost_submitted": False,
        "release_gate": "HOLD",
        "next_external_gate": "OWNER_AUTHORIZED_REAL_UGOS_ULIYA_RUNTIME_EVIDENCE",
    }
