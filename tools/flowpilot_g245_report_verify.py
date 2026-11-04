"""G245: explicitly approved digest verification of one G244 LOCAL output.

Operates on a persistent redacted G239 receipt. It never replays the source
CSV job, opens the original input, persists paths, or invokes native NAS.
The digest detects file corruption/changes, not adversarial DB tampering.
"""
from __future__ import annotations
import hashlib
import hmac
import re

from flowpilot_g238_local_csv_engine import LocalCsvRefused, _path, _read_once
from flowpilot_g239_csv_jobs import CsvJobRefused

JOB = re.compile(r"csv_[0-9a-f]{24}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
ACK = "APPROVE_LOCAL_REPORT_VERIFY_ONCE"


def verify_report(store, request_id: str, report_path: str,
                  acknowledgement: str) -> dict:
    if (type(request_id) is not str or JOB.fullmatch(request_id) is None
            or type(acknowledgement) is not str or acknowledgement != ACK):
        raise CsvJobRefused("G245_EXACT_REPORT_VERIFY_APPROVAL_REQUIRED", 403)
    if type(report_path) is not str or not 0 < len(report_path) <= 1024:
        raise CsvJobRefused("G245_ABSOLUTE_REPORT_PATH_REQUIRED", 403)
    try:
        path = _path(report_path)
    except LocalCsvRefused as exc:
        raise CsvJobRefused("G245_ABSOLUTE_REPORT_PATH_REQUIRED", 403) from exc
    if path.suffix.lower() != ".csv":
        raise CsvJobRefused("G245_ABSOLUTE_REPORT_PATH_REQUIRED", 403)
    receipt = store.readback(request_id)
    if (receipt.get("status") != "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS"
            or type(receipt.get("result")) is not dict
            or receipt["result"].get("report_file_created") is not True
            or receipt["result"].get("owner_source_modified") is not False
            or receipt["result"].get("nas_verified") is not False):
        raise CsvJobRefused("G245_APPROVED_OUTPUT_RECEIPT_REQUIRED", 403)
    expected = receipt["result"].get("report_sha256")
    if type(expected) is not str or SHA.fullmatch(expected) is None:
        raise CsvJobRefused("G245_INVALID_RECEIPT_HASH", 409)
    try:
        actual = hashlib.sha256(_read_once(path)).hexdigest()
    except LocalCsvRefused as exc:
        raise CsvJobRefused("G245_BOUNDED_REPORT_READ_REFUSED", 409) from exc
    equal = hmac.compare_digest(actual, expected)
    return {
        "schema":"flowpilot-g245-local-output-verify-v1",
        "request_id":request_id,
        "status":("VERIFIED_LOCAL_OUTPUT_SHA_NOT_NAS" if equal
                  else "CONFLICT_LOCAL_OUTPUT_SHA_NOT_NAS"),
        "expected_report_sha256":expected,
        "observed_report_sha256":actual,
        "matches_recorded_receipt":equal,
        "local_output_read_once":True,
        "original_input_reopened":False,
        "execution_replayed":False,
        "private_path_or_labels_included":False,
        "sqlite_mutated":False,
        "nas_verified":False,
        "release_gate":"HOLD",
    }
