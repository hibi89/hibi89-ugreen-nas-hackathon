"""G164: bounded CSV bytes reconstructed from actual code-owned synthetic QA receipt.

Never receives user filesystem paths, file contents or uncontrolled CSV inputs.
The G114 reference report SHA must match the bytes, not merely a test status.
"""
from __future__ import annotations

import csv
from hashlib import sha256
from io import StringIO

# Exact code-owned fixture bytes. Persisted SHA is a local integrity check;
# canonical content prevents an attacker from rewriting blob AND mutable SHA
# while leaving the separate G119 synthetic receipt untouched.
CANONICAL_CSV={
    "csv_customer_revenue_v1":
        b"customer,total_revenue\r\nalice,4.00\r\nbob,3.00\r\n",
    "required_file_metadata_v1":
        b"phase,required_1,required_2\r\ninitial,PRESENT,MISSING\r\n"
        b"after_fixture_repair,PRESENT,PRESENT\r\n",
}

class ArtifactRefused(ValueError):
    """Only synthetic fixture data allowed."""

def fixture_csv(template: str, evidence: object) -> bytes:
    if type(evidence) is not dict:
        raise ArtifactRefused("MISSING_SYNTHETIC_EVIDENCE")
    if template == "csv_customer_revenue_v1":
        rows=evidence.get("observed_rows")
        if rows != [["customer","total_revenue"],["alice","4.00"],["bob","3.00"]]:
            raise ArtifactRefused("UNTRUSTED_CSV_FIXTURE")
    elif template == "required_file_metadata_v1":
        if (evidence.get("initial_states")!=["PRESENT","MISSING"] or
            evidence.get("repaired_states")!=["PRESENT","PRESENT"] or
            evidence.get("source_fixture_preserved") is not True or
            evidence.get("file_contents_opened_by_adapter") is not False):
            raise ArtifactRefused("UNTRUSTED_FILE_METADATA_FIXTURE")
        rows=[["phase","required_1","required_2"],
              ["initial","PRESENT","MISSING"],["after_fixture_repair","PRESENT","PRESENT"]]
    else:
        raise ArtifactRefused("UNSUPPORTED_ARTIFACT_TEMPLATE")
    output=StringIO(newline="")
    csv.writer(output,lineterminator="\r\n").writerows(rows)
    blob=output.getvalue().encode("utf-8")
    if not 0<len(blob)<=4096:
        raise ArtifactRefused("ARTIFACT_BYTES_UNSAFE")
    if blob!=CANONICAL_CSV[template]:
        raise ArtifactRefused("NONCANONICAL_FIXTURE_CONTENT")
    if template == "csv_customer_revenue_v1" and evidence.get("report_sha256")!=sha256(blob).hexdigest():
        raise ArtifactRefused("EXECUTED_G114_REPORT_DIGEST_MISMATCH")
    return blob
