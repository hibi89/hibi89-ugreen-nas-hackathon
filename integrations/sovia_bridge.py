"""Synthetic-only LA-to-SOVIA advisory adapter (not a NAS execution gate)."""
from .ecosystem_contract import preflight_request

READ = frozenset(("literal", "field", "map", "condition", "branch", "csv_read",
                  "csv_normalize", "csv_filter", "sqlite_get"))
WRITE = frozenset(("sqlite_put", "sqlite_import_csv"))


class AdvisoryUnavailable(ValueError):
    pass


def assess_la_preview(request, preview, policy, assess):
    consent = preflight_request(request)
    if not consent.allowed:
        return {"allowed": False, "state": consent.state, "reason": consent.reason}
    if (not isinstance(preview, dict)
            or preview.get("scope") != "synthetic-local-only"
            or preview.get("executes_workflow") is not False
            or preview.get("source_version") not in ("azent.ir.v0", "axflow.ir.v0")):
        raise AdvisoryUnavailable("invalid LA preview")
    steps = preview.get("steps")
    if (type(steps) is not list or not 1 <= len(steps) <= 32
            or type(preview.get("step_count")) is not int
            or len(steps) != preview["step_count"]):
        raise AdvisoryUnavailable("invalid LA step count")
    if not callable(assess) or type(policy) is not dict:
        raise AdvisoryUnavailable("advisor or policy missing")
    safe = []
    for i, step in enumerate(steps, 1):
        if type(step) is not dict or set(step) != {"id", "op"}:
            raise AdvisoryUnavailable("unexpected LA metadata")
        operation = step["op"]
        if type(operation) is not str or operation not in READ | WRITE:
            raise AdvisoryUnavailable("unsupported LA operation")
        safe.append({"step_id": "step_" + str(i),
                     "tool_code": "la_" + operation,
                     "side_effect": "local_write" if operation in WRITE else "none"})
    if (preview.get("requires_write_approval") is True) != any(
            step["op"] in WRITE for step in steps):
        raise AdvisoryUnavailable("write approval metadata mismatch")
    reviewed = assess({"schema_version": "sovia.plan_review.v1",
                       "plan_ref": "ugreen_synthetic_plan",
                       "steps": safe}, policy)
    if (type(reviewed) is not dict
            or reviewed.get("schema_version") != "sovia.plan_review.v1"
            or reviewed.get("status") not in (
                "FINDINGS_REVIEW_REQUIRED", "NO_FINDINGS_STILL_UNVERIFIED")
            or reviewed.get("execution_authorized") is not False
            or reviewed.get("real_la_integration_verified") is not False
            or reviewed.get("offline_only") is not True
            or type(reviewed.get("finding_count")) is not int
            or not 0 <= reviewed["finding_count"] <= 1024):
        raise AdvisoryUnavailable("unverified SOVIA response")
    return {"allowed": True, "state": "ADVISORY_ONLY",
            "finding_count": reviewed["finding_count"],
            "execution_authorized": False, "nas_state": "NOT_CHECKED"}
