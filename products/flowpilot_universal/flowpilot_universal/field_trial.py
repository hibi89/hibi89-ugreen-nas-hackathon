"""Operator-initiated F09 repeatability evidence, never proof of physical hardware.

No auto-discovery, mounting, network calls, source writes or release approval.
Only explicitly consented, already-accessible local/USB/OS-mounted SMB directories.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

from .engine import InputError, _manifest_bytes, create_only
from .session import _safe_output, run_session, verify_history_entry

MEDIA = ("pc", "usb", "smb")


def run_field_trial(root: Path, manifest: Path, output: Path, *,
                    consent: bool = False, medium: str = "pc") -> dict:
    """Three independent full rehashes with create-only local evidence.

    A successful result means only that the selected *accessible* source was
    stable in this trial. It does NOT authenticate the claimed storage medium,
    SMB permissions, manufacturer, customer ownership, OS or commercial rights.
    """
    if consent is not True:
        raise InputError("operator must confirm ownership/permission and exact source scope")
    if medium not in MEDIA:
        raise InputError("medium must be pc, usb, or smb (operator-attested only)")
    output = _safe_output(root, output)
    manifest_bytes = _manifest_bytes(manifest)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    baseline = None
    entries: list[dict] = []
    verdict = "INCOMPLETE"
    reason = "three full scans not completed"
    for index in range(1, 4):
        try:
            if _manifest_bytes(manifest) != manifest_bytes:
                reason = "manifest changed between repeat scans"
                break
            session = run_session(root, manifest, output, consent=True, resume=False, pdf=False)
            verified = verify_history_entry(output, session.session_id)
            raw = session.json_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != verified["sha256"]:
                raise InputError("report altered after ledger verification")
            report = json.loads(raw)
            if verified["reports_verified"] != 2 or verified["status"] != session.status:
                raise InputError("report verification disagreement")
            signature = hashlib.sha256(json.dumps(
                [(x["path"], x["size"], x["sha256"]) for x in report["files"]],
                ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            entries.append({
                "round": index, "session_id": session.session_id,
                "status": session.status, "files_scanned": session.scanned,
                "reports_verified": verified["reports_verified"],
                "file_list_sha256": signature, "report_sha256": verified["sha256"],
            })
            if session.status != "READY":
                reason = "scan not READY: " + session.status
                break
            if baseline is not None and baseline != signature:
                reason = "source file list/size/hash differs across rounds"
                break
            baseline = signature
        except (InputError, OSError, ValueError, KeyError, TypeError) as exc:
            reason = "round evidence failure: " + type(exc).__name__
            break
    else:
        if _manifest_bytes(manifest) == manifest_bytes:
            verdict = "REPEATABILITY_PASS_NOT_FIELD_ACCEPTANCE"
            reason = "three full scans stable; physical medium and rights not authenticated"
        else:
            reason = "manifest changed after final scan"

    summary = {
        "schema_version": 1,
        "verdict": verdict, "reason": reason,
        "medium_claim_unverified": medium,
        "source_scope": str(root.resolve(strict=True)),
        "manifest_sha256": manifest_sha256,
        "offline": True, "no_source_writes": True,
        "customer_hardware_verified": False,
        "commercial_acceptance": False,
        "rounds": entries,
    }
    path = output / ("flowpilot-field-trial-" + uuid4().hex + ".json")
    create_only(path, json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", root)
    return {"summary_path": str(path), **summary}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Consent-only local three-pass field-readiness check")
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--medium", choices=MEDIA, required=True, help="Operator claim, not automatic media verification")
    parser.add_argument("--consent", action="store_true", help="Confirm legal access and exact read-only source scope")
    args = parser.parse_args(argv)
    try:
        result = run_field_trial(args.root, args.manifest, args.output,
                                 consent=args.consent, medium=args.medium)
        # PyInstaller --windowed executables may provide no stdio handles.
        # Keep the persistent local summary as the authoritative result.
        if sys.stdout is not None:
            print(result["verdict"] + " rounds=" + str(len(result["rounds"]))
                  + " local_summary=" + result["summary_path"])
        return 0 if result["verdict"] == "REPEATABILITY_PASS_NOT_FIELD_ACCEPTANCE" else 2
    except (InputError, OSError) as exc:
        if sys.stderr is not None:
            print("HOLD: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
