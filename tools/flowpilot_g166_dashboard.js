"use strict";
// G166: browser state is intentionally ephemeral. No cookies, storage or token in URLs.
const el = id => document.getElementById(id);
const controls = [...document.querySelectorAll("button")];
let token = "", workflow = null, verifiedPlan = null, review = null, lastLocalReport = null, busy = false;
let csvTicket = null, csvJobId = null, csvReceipt = null;
let csvBoundReportPath = null; // ephemeral reviewed destination, never persisted
function clearCsv() {
  csvTicket = null; csvJobId = null; csvReceipt = null;
  csvBoundReportPath = null;
  el("csv-verify-path").value = "";
  el("csv-verify-consent").checked = false;
  el("csv-local-path").value = "";
  el("csv-report-path").value = "";
  el("csv-report-consent").checked = false;
  el("csv-intent").value = "";
  el("csv-recover-id").value = "";
  el("csv-history-consent").checked = false;
  el("csv-history-select").replaceChildren(new Option("선택 안 함", ""));
  el("csv-export-consent").checked = false;
  el("csv-consent").checked = false;
  el("csv-job-status").textContent = "CSV 계획 미확인 · 입력 경로 미저장 · NAS 미검증";
}
function status(message) { el("notice").textContent = message; }
function output(data) { el("output").textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2); }
// G250: only allowlisted evidence fields may leave the browser; no HTTP write.
function revokeVersionExport() { el("version-export-consent").checked = false; }
function versionEvidence(x) {
  if (!x || x.schema !== "flowpilot-owner-local-metadata-session-v1" ||
      x.selected_intent !== "REVIEW_VERSIONS" ||
      !["LOCAL_METADATA_FINDINGS_READY","LOCAL_METADATA_BLOCKED"].includes(x.status) ||
      x.approved_local_metadata_access !== true ||
      x.file_contents_opened !== false || x.raw_filenames_returned !== false ||
      x.owner_root_returned !== false || x.nas_verified !== false ||
      x.registered_expert_invoked !== false || x.release_gate !== "HOLD" ||
      typeof x.scope_sha256 !== "string" || !/^[0-9a-f]{64}$/.test(x.scope_sha256) ||
      !Number.isInteger(x.required_count) || x.required_count < 1 || x.required_count > 20 ||
      !Number.isInteger(x.version_candidate_count) ||
      x.version_candidate_count < 1 || x.version_candidate_count > 20 ||
      !Array.isArray(x.typed_review_plan) || x.typed_review_plan.length !== 4 ||
      x.typed_review_plan[0]?.access !== "READ" ||
      x.typed_review_plan.slice(1).some(s=>s?.access !== "COMPUTE") ||
      !Array.isArray(x.inspection_result) || x.inspection_result.length !== x.required_count)
    throw Error("검증된 로컬 버전 증거만 내보낼 수 있습니다.");
  const findings=x.inspection_result.map((row,i)=>{
    if (!row || row.index !== i+1 ||
        !["PRESENT","MISSING","NOT_CHECKED","VERSION_REVIEW"].includes(row.state))
      throw Error("버전 증거의 인덱스/상태 검증 실패");
    return {index:i+1,state:row.state};
  });
  return {
    schema:"flowpilot-local-version-evidence-g249-v1",
    status:"REDACTED_LOCAL_VERSION_EVIDENCE_NOT_NAS",
    scope_sha256:x.scope_sha256,
    required_count:x.required_count,
    version_candidate_count:x.version_candidate_count,
    stages:["SCOPED_READ","VERSION_COMPARE","OWNER_REVIEW","REDACTED_EVIDENCE"],
    findings,
    manual_owner_review_required:findings.some(row=>row.state==="VERSION_REVIEW"),
    auto_selected_final_version:false,
    owner_file_contents_opened:false,
    original_files_modified:false,
    owner_paths_included:false,
    nas_verified:false,
    release_gate:"HOLD"
  };
}
const adviceFields = [
  ["advice-disk", "disk_used_percent", 100],
  ["advice-errors", "repeated_error_count", 87600],
  ["advice-backup", "backup_age_hours", 87600]
];
function clearAdvice() {
  for (const [id] of adviceFields) el(id).value = "";
  el("advice-consent").checked = false;
  el("advice-summary").textContent = "동의 전 · 수치 미전송 · 자동 감시 없음";
}
function sync() {
  el("workflow-id").textContent = workflow?.workflow_id || "없음";
  el("workflow-state").textContent = workflow?.status === "UNKNOWN_REQUIRES_READBACK" ?
    "결과 미확인 · 조회 필요" : workflow?.status || "미생성";
  el("plan-hash").textContent = verifiedPlan ? "검증한 계획 SHA-256: " + verifiedPlan :
    "계획 SHA-256: 미확인";
  el("local-council-state").textContent = lastLocalReport ?
    "실제 로컬 보고서 " + lastLocalReport.verdict + " · NAS 미검증" :
    "실제 로컬 증거 미검토 · NAS 미검증";
  el("metadata-summary").textContent = review ? "검토 ID: " + review.review_id +
    " | 상태: " + review.status + " | 항목: " + review.required_count +
    " | 범위 SHA-256: " + review.scope_sha256 : "검토 세션 없음";
  for (const button of controls) {
    if (button.id === "connect" || button.id === "disconnect" || button.id === "clear") {
      button.disabled = busy; continue;
    }
    if (!token || busy) { button.disabled = true; continue; }
    const s = workflow?.status;
    const rules = {
      load: !!el("existing").value,
      refresh: !!workflow?.workflow_id,
      plan: !!workflow && workflow.status !== "UNKNOWN_REQUIRES_READBACK",
      guide: !!workflow && workflow.status !== "UNKNOWN_REQUIRES_READBACK",
      "advice-submit": el("advice-consent").checked &&
        adviceFields.some(([id]) => el(id).value !== ""),
      test: s === "PLANNED", approve: s === "TESTED" && !!verifiedPlan && el("synthetic-consent").checked,
      run: s === "APPROVED_SYNTHETIC",
      audit: !!workflow && s !== "UNKNOWN_REQUIRES_READBACK",
      evidence: s === "COMPLETE_LOCAL_SYNTHETIC", report: s === "COMPLETE_LOCAL_SYNTHETIC",
      recover: s === "RUNNING", "meta-approve": review?.status === "WAITING_APPROVAL" && el("metadata-consent").checked,
      "meta-cancel": review?.status === "WAITING_APPROVAL", "meta-status": !!review,
      "version-export": review?.selected_intent === "REVIEW_VERSIONS" &&
        ["LOCAL_METADATA_FINDINGS_READY","LOCAL_METADATA_BLOCKED"].includes(review?.status) &&
        el("version-export-consent").checked,
      "meta-save": workflow?.template === "required_file_metadata_v1" &&
        ["LOCAL_METADATA_FINDINGS_READY", "LOCAL_METADATA_BLOCKED"].includes(review?.status) &&
        el("meta-save-consent").checked,
      "meta-readback": workflow?.template === "required_file_metadata_v1",
      "text-preview": workflow?.template === "required_file_metadata_v1",
      "meta-council": workflow?.template === "required_file_metadata_v1",
      "meta-report": workflow?.template === "required_file_metadata_v1",
      "native-handoff": workflow?.template === "required_file_metadata_v1",
      "meta-export": !!lastLocalReport && workflow?.template === "required_file_metadata_v1",
      "csv-preview": true,
      "csv-intent-apply": true,
      "version-intent-apply": true,
      "csv-run": !!csvTicket && el("csv-consent").checked &&
        csvBoundReportPath !== null &&
        el("csv-report-path").value === csvBoundReportPath &&
        ((!el("csv-report-path").value && !el("csv-report-consent").checked) ||
         (!!el("csv-report-path").value && el("csv-report-consent").checked)),
      "csv-readback": !!csvJobId,
      "csv-recover": true,
      "csv-history-list": el("csv-history-consent").checked,
      "csv-history-open": !!el("csv-history-select").value,
      "csv-verify-report": !!csvReceipt &&
        csvReceipt.status === "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS" &&
        csvReceipt.result?.report_file_created === true &&
        !!el("csv-verify-path").value && el("csv-verify-consent").checked,
      "csv-export": !!csvReceipt && el("csv-export-consent").checked
    };
    button.disabled = Object.prototype.hasOwnProperty.call(rules, button.id) && !rules[button.id];
  }
}
async function api(path, body, historyReview = false) {
  if (!token) throw Error("로컬 API 연결이 필요합니다.");
  const headers = { "Authorization": "Bearer " + token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (historyReview) headers["X-Local-Receipt-Review"] = "APPROVE_LOCAL_CSV_HISTORY_READ_ONCE";
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST", headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store", credentials: "omit", mode: "same-origin", redirect: "error"
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    throw Error("HTTP " + response.status + " · " + (problem.error || "LOCAL_REQUEST_FAILED"));
  }
  return response;
}
async function json(path, body, historyReview = false) { return (await api(path, body, historyReview)).json(); }
async function act(fn) {
  if (busy) return;
  busy = true; sync();
  try { await fn(); } catch (error) {
    status("요청 거부 또는 연결 오류 · " + error.message);
    output({ status: "REFUSED_OR_OFFLINE", reason: error.message, real_nas_tested: false });
  } finally { busy = false; sync(); }
}
function resetWorkflow(result) {
  workflow = result;
  verifiedPlan = null;
  review = null;
  revokeVersionExport();
  el("metadata-consent").checked = false;
  el("meta-save-consent").checked = false;
  lastLocalReport = null;
  el("synthetic-consent").checked = false;
  el("meta-save-consent").checked = false;
  sync();
}
function randomRequestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return "req_" + Array.from(bytes, x => x.toString(16).padStart(2, "0")).join("");
}
el("connect").addEventListener("click", () => act(async () => {
  const input = el("token");
  const candidate = input.value;
  input.value = "";
  // A new login attempt invalidates any previous authority even if input is bad.
  token = ""; workflow = null; verifiedPlan = null; review = null; lastLocalReport = null;
  el("synthetic-consent").checked = false; el("metadata-consent").checked = false; el("meta-save-consent").checked = false;
  el("required").value = ""; el("version-candidates").value = ""; el("text-workflow").value = ""; el("version-intent").value = ""; revokeVersionExport(); clearAdvice(); clearCsv();
  el("existing").replaceChildren(new Option("선택 안 함", ""));
  el("connection-status").textContent = "기존 세션 폐기 · 인증 확인 중";
  if (candidate.length < 32 || candidate.length > 256) throw Error("토큰 길이는 32–256자여야 합니다.");
  token = candidate;
  try {
    const response = await json("/v1/health");
    if (response.status !== "LOCAL_BACKEND_READY" || response.release_gate !== "HOLD")
      throw Error("알 수 없는 API 응답");
    el("connection-status").textContent = "로컬 연결 확인 · 인증 토큰은 메모리에만 유지";
    status("로컬 인증 성공 · NAS 체험 미사용");
    output(response);
  } catch (error) { token = ""; el("connection-status").textContent = "연결 실패 · 토큰 폐기"; throw error; }
}));
el("disconnect").addEventListener("click", () => {
  token = ""; workflow = null; verifiedPlan = null; review = null; lastLocalReport = null;
  el("token").value = ""; el("required").value = ""; el("version-candidates").value = ""; el("text-workflow").value = ""; el("version-intent").value = ""; revokeVersionExport(); clearAdvice(); clearCsv();
  el("existing").replaceChildren(new Option("선택 안 함", ""));
  el("synthetic-consent").checked = false; el("metadata-consent").checked = false; el("meta-save-consent").checked = false;
  el("connection-status").textContent = "연결 해제 · 토큰 폐기";
  status("로컬 세션 연결 해제"); output("토큰은 저장되지 않습니다."); sync();
});
el("create").addEventListener("click", () => act(async () => {
  const goal = el("goal").value;
  // A new request may have committed even if its reply was lost. Revoke old
  // workflow authority BEFORE dispatch, not only after a successful response.
  resetWorkflow(null);
  const result = await json("/v1/workflows", {goal, request_id: randomRequestId()});
  if (result.schema !== "flowpilot-backend-local-v1" ||
      !/^wf_[0-9a-f]{32}$/.test(result.workflow_id || "") ||
      result.status !== "PLANNED" || result.synthetic_only !== true ||
      result.nas_verified !== false || result.release_gate !== "HOLD" ||
      !/^[a-f0-9]{64}$/.test(result.plan_sha256 || "") ||
      result.event_count !== 1)
    throw Error("생성 응답 검증 실패 · 목록에서 읽기 전용으로 확인하세요");
  resetWorkflow(result); status("합성 계획 생성 · 명시적 테스트와 승인 필요"); output(result);
}));
el("list").addEventListener("click", () => act(async () => {
  const result = await json("/v1/workflows");
  const names = {
    required_file_metadata_v1: "필수 파일 점검 (합성)",
    csv_customer_revenue_v1: "고객별 매출 보고서 (합성)"
  };
  const states = new Set(["PLANNED","TESTED","APPROVED_SYNTHETIC",
    "RUNNING","COMPLETE_LOCAL_SYNTHETIC","BLOCKED","INTERRUPTED_BLOCKED"]);
  if (result.status !== "LOCAL_WORKFLOW_LIST" || result.release_gate !== "HOLD" ||
      result.nas_verified !== false || !Array.isArray(result.workflows) ||
      result.workflows.length > 20 || result.count !== result.workflows.length ||
      !result.workflows.every(id => /^wf_[0-9a-f]{32}$/.test(id)) ||
      new Set(result.workflows).size !== result.workflows.length)
    throw Error("워크플로 목록 응답 검증 실패");
  // Be compatible with earlier local backends returning only workflow IDs.
  const detailed = Array.isArray(result.summaries);
  if (detailed && (result.summaries.length !== result.workflows.length ||
      !result.summaries.every((item, i) => item.workflow_id === result.workflows[i] &&
        Object.prototype.hasOwnProperty.call(names, item.template) &&
        states.has(item.status))))
    throw Error("목록 템플릿·상태 검증 실패");
  const select = el("existing");
  select.replaceChildren(new Option("선택 안 함", ""));
  for (let i = 0; i < result.workflows.length; i++) {
    const id = result.workflows[i];
    const item = detailed ? result.summaries[i] : null;
    // Labels are derived from code-owned template names, never stored goal text.
    const label = item ? names[item.template] + " · " + item.status + " · " + id.slice(-6) : id;
    select.add(new Option(label, id));
  }
  status("검증된 로컬 워크플로 상태 목록 · 재개하려면 선택 후 불러오기");
  output({status:result.status, count:result.count, summaries:result.summaries || [],
    nas_verified:false, release_gate:"HOLD"});
}));
el("load").addEventListener("click", () => act(async () => {
  const id = el("existing").value;
  // A failed or forged GET must not leave the previously approved workflow
  // actionable. Never treat a response for a different ID as this selection.
  resetWorkflow(null);
  if (!/^wf_[0-9a-f]{32}$/.test(id)) throw Error("워크플로 ID를 선택하세요.");
  const result = await json("/v1/workflows/" + id);
  const states = ["PLANNED","TESTED","APPROVED_SYNTHETIC","RUNNING",
    "COMPLETE_LOCAL_SYNTHETIC","BLOCKED","INTERRUPTED_BLOCKED"];
  const templates = ["required_file_metadata_v1","csv_customer_revenue_v1"];
  if (result.workflow_id !== id || result.schema !== "flowpilot-backend-local-v1" ||
      !states.includes(result.status) || !templates.includes(result.template) ||
      !/^[a-f0-9]{64}$/.test(result.plan_sha256 || "") ||
      result.release_gate !== "HOLD" || result.synthetic_only !== true ||
      result.nas_verified !== false || result.registered_expert_invoked !== false ||
      !Number.isInteger(result.event_count) || result.event_count < 1)
    throw Error("저장된 상태 응답 검증 실패 · 이전 승인 사용 불가");
  resetWorkflow(result);
  status("기존 상태 로드 · 이전 승인 체크는 유지하지 않음"); output(workflow);
}));
el("plan").addEventListener("click", () => act(async () => {
  if (!workflow) throw Error("계획이 없습니다.");
  const result = await json("/v1/workflows/" + workflow.workflow_id + "/plan");
  if (result.workflow_id !== workflow.workflow_id ||
      result.plan_sha256 !== workflow.plan_sha256 || result.release_gate !== "HOLD")
    throw Error("계획 해시와 워크플로가 일치하지 않습니다.");
  verifiedPlan = result.plan_sha256;
  el("synthetic-consent").checked = false;
  status("계획 해시 확인 · 별도 합성 승인 필요"); output(result);
}));
el("guide").addEventListener("click", () => act(async () => {
  if (!workflow) throw Error("가이드를 표시할 워크플로가 없습니다.");
  const result = await json("/v1/workflows/" + workflow.workflow_id + "/guide");
  if (result.workflow_id !== workflow.workflow_id ||
      result.plan_sha256 !== workflow.plan_sha256 ||
      result.workflow_state !== workflow.status ||
      result.status !== "SYNTHETIC_OPERATOR_GUIDE_READY_NOT_NAS" ||
      result.release_gate !== "HOLD" || result.real_nas_verified !== false ||
      result.commands_executed !== false || result.owner_files_accessed !== false ||
      result.total_local_steps !== 6 ||
      !Number.isInteger(result.verified_local_steps) ||
      result.verified_local_steps < 0 || result.verified_local_steps > 6 ||
      !Array.isArray(result.steps) || result.steps.length !== 7 ||
      !result.steps.every((step, idx) => step.number === idx + 1 &&
        ["VERIFIED_LOCAL","NEXT","WAITING","RECOVERY_REQUIRED","STOPPED","OFFICIAL_BLOCKED"].includes(step.progress)) ||
      result.steps[6].progress !== "OFFICIAL_BLOCKED" ||
      typeof result.next_action !== "string" ||
      !/^[0-9a-f]{64}$/.test(result.guide_sha256))
    throw Error("가이드 출처 또는 현재 상태 일치 검증 실패");
  // Verify the API-owned SHA against a canonical serialization in-browser.
  // Python: json.dumps(sort_keys=True,separators=(',', ':'),ensure_ascii=True).
  function canonical(value) {
    if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
    if (value !== null && typeof value === "object")
      return "{" + Object.keys(value).sort().map(key =>
        canonical(key) + ":" + canonical(value[key])).join(",") + "}";
    const serialized = JSON.stringify(value);
    return typeof value === "string" ? serialized.replace(/[\u007f-\uffff]/g,
      char => "\\u" + char.charCodeAt(0).toString(16).padStart(4,"0")) : serialized;
  }
  const copy = {...result}; delete copy.guide_sha256;
  const hash = await crypto.subtle.digest("SHA-256",
    new TextEncoder().encode(canonical(copy)));
  const verified = Array.from(new Uint8Array(hash),
    x => x.toString(16).padStart(2,"0")).join("");
  if (verified !== result.guide_sha256)
    throw Error("가이드 SHA-256 무결성 오류");
  const lines = [
    "FlowPilot 3.0 · 합성 전용 7단계 운영 가이드",
    "실제 NAS / Uliya / Docker 실행 검증 아님 · RELEASE HOLD",
    "현재 실행 상태: " + result.workflow_state,
    "로컬 검증 단계: " + result.verified_local_steps + "/6 · 공식 승인 별도",
    "다음 작업: " + result.next_action,
    "계획 SHA-256: " + result.plan_sha256,
    "가이드 SHA-256: " + result.guide_sha256 + " (브라우저 대조 완료)",
    "",
    ...result.steps.map((step, idx) =>
      (idx + 1) + ". [" + step.progress + "] " + step.title + "\n  " +
      step.instruction + "\n  예상 결과: " + step.expected)
  ];
  status("단계별 운영 안내 표시 · 코드를 실행하지 않았습니다.");
  output(lines.join("\n"));
}));
el("test").addEventListener("click", () => act(async () => {
  resetWorkflow(await json("/v1/workflows/" + workflow.workflow_id + "/test", {}));
  status("4역할 합성 테스트 완료 · 다시 계획 해시 확인 필요"); output(workflow);
}));
el("approve").addEventListener("click", () => act(async () => {
  if (workflow?.status !== "TESTED" || verifiedPlan !== workflow.plan_sha256 ||
      !el("synthetic-consent").checked) throw Error("TESTED · 해시 확인 · 명시적 동의가 필요합니다.");
  const id = workflow.workflow_id;
  const hash = verifiedPlan;
  // The server may commit an approval even when its response is lost.
  // Revoke the one-use consent and all executable authority BEFORE POST.
  // Only explicit GET readback may restore the verified server state.
  resetWorkflow({workflow_id:id, status:"UNKNOWN_REQUIRES_READBACK"});
  const result = await json("/v1/workflows/" + id + "/approve", {
    plan_sha256: hash, acknowledgement: "APPROVE_SYNTHETIC_ONLY"
  });
  if (result.workflow_id !== id || result.status !== "APPROVED_SYNTHETIC" ||
      result.plan_sha256 !== hash || result.synthetic_only !== true ||
      result.nas_verified !== false || result.registered_expert_invoked !== false ||
      result.release_gate !== "HOLD" || !Number.isInteger(result.event_count) ||
      result.event_count < 3)
    throw Error("합성 승인 응답 미확정 · 읽기 전용 상태 조회가 필요합니다.");
  resetWorkflow(result);
  status("합성 실행만 승인됨 · NAS 접근 미승인"); output(workflow);
}));
el("refresh").addEventListener("click", () => act(async () => {
  const id = workflow?.workflow_id;
  if (!/^wf_[0-9a-f]{32}$/.test(id || "")) throw Error("조회할 워크플로가 없습니다.");
  // GET-only reconciliation; it never executes, approves, or retries a POST.
  const result = await json("/v1/workflows/" + id);
  const states = ["PLANNED","TESTED","APPROVED_SYNTHETIC","RUNNING",
    "COMPLETE_LOCAL_SYNTHETIC","BLOCKED","INTERRUPTED_BLOCKED"];
  const templates = ["required_file_metadata_v1","csv_customer_revenue_v1"];
  if (result.workflow_id !== id || !states.includes(result.status) ||
      !templates.includes(result.template) || !/^[a-f0-9]{64}$/.test(result.plan_sha256) ||
      result.release_gate !== "HOLD" || result.synthetic_only !== true ||
      result.nas_verified !== false || !Number.isInteger(result.event_count) ||
      result.event_count < 1)
    throw Error("저장된 상태 응답 검증 실패 · 재실행 금지");
  resetWorkflow(result);
  status(result.status === "RUNNING" ?
    "실행 예약 상태 · 재실행 금지, 중단 작업 복구 조회 필요" :
    result.status === "COMPLETE_LOCAL_SYNTHETIC" ?
    "서버 기록으로 합성 완료 확인 · 실행 재요청 없음" :
    "서버 저장 상태 확인: " + result.status + " · 이전 동의 재사용 불가");
  output(result);
}));
el("run").addEventListener("click", () => act(async () => {
  if (workflow?.status !== "APPROVED_SYNTHETIC") throw Error("승인된 합성 실행만 가능합니다.");
  const id = workflow.workflow_id;
  // Mark the browser state unknown BEFORE the POST. If the response is lost
  // after SQLite commit, we must never leave an enabled duplicate Run button.
  workflow = {workflow_id:id, status:"UNKNOWN_REQUIRES_READBACK"};
  verifiedPlan = null;
  el("synthetic-consent").checked = false;
  sync();
  const result = await json("/v1/workflows/" + id + "/run", {});
  if (result.workflow_id !== id || result.synthetic_only !== true ||
      result.release_gate !== "HOLD" ||
      !["COMPLETE_LOCAL_SYNTHETIC","BLOCKED"].includes(result.status))
    throw Error("합성 실행 응답 미확정 · 현재 상태를 읽기 전용으로 확인하세요");
  resetWorkflow(result);
  status(result.status === "COMPLETE_LOCAL_SYNTHETIC" ?
    "로컬 합성 실행 완료 · 감사·CSV 별도 확인" :
    "합성 실행 차단 · 자동 재시도 금지, 감사 조회 필요");
  output(result);
}));
for (const name of ["audit", "evidence"]) {
  el(name).addEventListener("click", () => act(async () => {
    const result = await json("/v1/workflows/" + workflow.workflow_id + "/" + name);
    status(name === "audit" ? "로컬 해시 체인 조회" : "로컬 합성 증거 조회"); output(result);
  }));
}
el("recover").addEventListener("click", () => act(async () => {
  resetWorkflow(await json("/v1/workflows/" + workflow.workflow_id + "/recover", {}));
  status("복구 조회 완료 · 중단된 실행은 자동 재시도하지 않습니다."); output(workflow);
}));
el("report").addEventListener("click", () => act(async () => {
  if (workflow?.status !== "COMPLETE_LOCAL_SYNTHETIC") throw Error("완료된 합성 실행이 필요합니다.");
  const response = await api("/v1/workflows/" + workflow.workflow_id + "/report");
  if (!(response.headers.get("Content-Type") || "").startsWith("text/csv"))
    throw Error("CSV 응답 타입 불일치");
  const declared = response.headers.get("X-Flowpilot-Content-SHA256") || "";
  const bytes = await response.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const computed = Array.from(new Uint8Array(digest), x => x.toString(16).padStart(2, "0")).join("");
  if (!/^[0-9a-f]{64}$/.test(declared) || computed !== declared)
    throw Error("보고서 SHA-256 불일치 · 다운로드 차단");
  const url = URL.createObjectURL(new Blob([bytes], {type:"text/csv;charset=utf-8"}));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = "flowpilot-synthetic-fixture.csv";
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status("합성 CSV SHA-256 검증 및 다운로드 요청 완료");
  output({status:"LOCAL_SYNTHETIC_CSV_SHA_VERIFIED", sha256:computed, byte_length:bytes.byteLength, real_nas_verified:false});
}));
// G254: local allowlisted text mapping; never reads source or contacts server.
el("version-intent-apply").addEventListener("click", () => act(async () => {
  const raw = el("version-intent").value;
  el("version-intent").value = "";
  // Even invalid text revokes previous browser review and approvals.
  review = null; lastLocalReport = null;
  el("metadata-consent").checked = false;
  el("meta-save-consent").checked = false;
  revokeVersionExport();
  el("required").value = "";
  el("version-candidates").value = "";
  el("text-workflow").value = "";
  const matched = typeof raw === "string" && raw.length <= 300 ?
    /^(버전 비교|compare versions)\s*:\s*(\S+)\s*=>\s*(\S+)$/i.exec(raw.trim()) : null;
  if (!matched) throw Error("지원된 단일 버전 비교 문법이 아닙니다.");
  const required = matched[2], candidate = matched[3];
  const safe = value => value.length <= 120 &&
    /^[A-Za-z0-9._-]+(?:\/[A-Za-z0-9._-]+){0,5}$/.test(value) &&
    value.split("/").every(part => part !== "." && part !== ".." &&
      !part.startsWith(".") && !part.endsWith("."));
  if (!safe(required) || !safe(candidate) || required === candidate)
    throw Error("허용되지 않은 상대 파일 범위입니다.");
  el("metadata-goal").value = matched[1] === "버전 비교" ?
    "버전 비교해줘" : "review versions";
  el("required").value = required;
  el("version-candidates").value = required + "=" + candidate;
  status("버전 비교 범위 구조화 · 파일 미조회 · 별도 계획 미리보기 필요");
  output({schema:"flowpilot-g254-scoped-version-intent-v1",
    status:"LOCAL_TYPED_VERSION_SCOPE_NO_READ", selected_intent:"REVIEW_VERSIONS",
    required_count:1, version_candidate_count:1, local_metadata_read:false,
    requires_separate_preview:true, requires_explicit_read_approval:true,
    auto_selected_final_version:false, nas_verified:false, release_gate:"HOLD"});
}));
el("meta-preview").addEventListener("click", () => act(async () => {
  // Starting a NEW review must revoke old consent/review even when the new
  // input is invalid or the HTTP preview is refused. Clear raw paths first.
  const raw = el("required").value;
  const rawVersions = el("version-candidates").value;
  const versionGoal = el("metadata-goal").value;
  el("version-intent").value = "";
  el("required").value = "";
  el("version-candidates").value = "";
  el("text-workflow").value = "";
  lastLocalReport = null;
  review = null;
  el("metadata-consent").checked = false;
  el("meta-save-consent").checked = false;
  revokeVersionExport();
  const required = raw.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if (required.length < 1 || required.length > 20) throw Error("경로 1–20개가 필요합니다.");
  const lines = rawVersions.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if (lines.length > 20) throw Error("버전 후보는 최대 20개입니다.");
  const versions = Object.create(null);
  for (const line of lines) {
    const parts = line.split("=");
    if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim())
      throw Error("버전 후보는 필수경로=후보경로 형식이어야 합니다.");
    const key = parts[0].trim(), value = parts[1].trim();
    if (!required.includes(key)) throw Error("버전 후보는 선택한 필수경로에만 연결할 수 있습니다.");
    if (!Object.prototype.hasOwnProperty.call(versions,key)) versions[key] = [];
    versions[key].push(value);
    if (versions[key].length > 5) throw Error("한 필수경로당 후보 5개 이내입니다.");
  }
  if (!["check required files","review versions","버전 비교해줘"].includes(versionGoal))
    throw Error("허용되지 않은 로컬 점검 의도");
  if (versionGoal !== "check required files" && !lines.length)
    throw Error("버전 비교에는 정확한 후보 파일 관계가 필요합니다.");
  const args = {goal:versionGoal,required};
  if (lines.length) args.versions = versions;
  const plan = await json("/v1/local-metadata/preview", args);
  const isVersion = versionGoal !== "check required files";
  if (plan.schema !== "flowpilot-owner-local-metadata-session-v1" ||
      plan.status !== "WAITING_APPROVAL" || plan.release_gate !== "HOLD" ||
      plan.nas_verified !== false ||
      plan.selected_intent !== (isVersion ? "REVIEW_VERSIONS" : "CHECK_REQUIRED") ||
      plan.approved_local_metadata_access !== false ||
      plan.file_contents_opened !== false || plan.raw_filenames_returned !== false ||
      plan.owner_root_returned !== false ||
      !/^[a-f0-9]{64}$/.test(plan.scope_sha256 || "") ||
      (isVersion && (!Array.isArray(plan.typed_review_plan) ||
        plan.typed_review_plan.length !== 4 ||
        plan.typed_review_plan[0].access !== "READ" ||
        plan.typed_review_plan.slice(1).some(step => step.access !== "COMPUTE"))))
    throw Error("버전 검토 계획이 안전성 계약과 다릅니다.");
  review = plan;
  status(isVersion ?
    "명시된 버전 후보 읽기 전 4단계 계획 확인 · 별도 1회 동의 필요" :
    "로컬 메타데이터 읽기 전 미리보기 · 아직 파일 미조회");
  output(review);
}));
el("text-preview").addEventListener("click", () => act(async () => {
  const raw = el("text-workflow").value;
  el("version-intent").value = "";
  el("text-workflow").value = "";
  el("required").value = "";
  el("version-candidates").value = "";
  review = null;
  lastLocalReport = null;
  el("metadata-consent").checked = false;
  el("meta-save-consent").checked = false;
  revokeVersionExport();
  if (!workflow || workflow.template !== "required_file_metadata_v1")
    throw Error("먼저 필수 파일 워크플로를 생성하거나 불러오세요.");
  if (!raw || raw.length > 1100) throw Error("다단계 명령 1–1100자가 필요합니다.");
  review = await json("/v1/local-metadata/text-preview",
                      {workflow_id:workflow.workflow_id,instructions:raw});
  if (review.status !== "WAITING_APPROVAL" ||
      review.bound_workflow_id !== workflow.workflow_id ||
      !(review.parsed_actions_count >= 1 && review.parsed_actions_count <= 8))
    throw Error("다단계 검토 응답이 유효하지 않습니다.");
  status("다단계 요구사항 구조화 · 원본 파일 미조회 · 별도 1회 승인 필요");
  output(review);
}));
el("meta-approve").addEventListener("click", () => act(async () => {
  if (!review || review.status !== "WAITING_APPROVAL" || !el("metadata-consent").checked)
    throw Error("검토 및 별도 동의가 필요합니다.");
  // Exact one-use approval can be consumed server-side even when the client
  // never receives the reply. Never keep an actionable ticket after dispatch.
  const ticket = review;
  review = null;
  revokeVersionExport();
  el("metadata-consent").checked = false;
  review = await json("/v1/local-metadata/approve", {
    review_id:ticket.review_id, scope_sha256:ticket.scope_sha256,
    acknowledgement:"APPROVE_LOCAL_METADATA_READ_ONLY"
  });
  status("로컬 메타데이터 1회 읽기 종료 · NAS 검증 아님"); output(review);
}));
el("meta-cancel").addEventListener("click", () => act(async () => {
  if (!review || review.status !== "WAITING_APPROVAL") throw Error("취소 가능한 검토 없음");
  // A cancel may be accepted server-side while the client loses the reply.
  // Revoke the browser's ticket/consent before dispatch, even on HTTP failure.
  const reviewId = review.review_id;
  review = null;
  revokeVersionExport();
  el("metadata-consent").checked = false;
  el("required").value = "";
  el("version-candidates").value = "";
  el("text-workflow").value = "";
  const canceled = await json("/v1/local-metadata/cancel", {review_id:reviewId});
  if (canceled.review_id !== reviewId || canceled.status !== "CANCELED" ||
      canceled.approved_local_metadata_access !== false)
    throw Error("취소 응답 검증 실패 · 새로운 검토가 필요합니다.");
  review = canceled;
  status("검토 취소 확인 · 메타데이터 읽기 없음"); output(review);
}));
el("meta-status").addEventListener("click", () => act(async () => {
  if (!review) throw Error("검토 세션 없음");
  revokeVersionExport();
  review = await json("/v1/local-metadata/reviews/" + review.review_id);
  status("저장된 메모리 내 메타데이터 상태 재조회 · 재실행 없음"); output(review);
}));
el("version-export").addEventListener("click", () => act(async () => {
  if (!review || !el("version-export-consent").checked)
    throw Error("검토 완료 및 별도 저장 동의가 필요합니다.");
  revokeVersionExport();
  const proof=versionEvidence(review);
  const text=JSON.stringify(proof,null,2)+"\n";
  if (text.length>10000) throw Error("저장할 버전 증거가 너무 큽니다.");
  const url=URL.createObjectURL(new Blob([text],{type:"application/json;charset=utf-8"}));
  try {
    const a=document.createElement("a");
    a.href=url; a.download="flowpilot-local-version-evidence.json";
    document.body.append(a); a.click(); a.remove();
  } finally { setTimeout(()=>URL.revokeObjectURL(url),1000); }
  status("별도 승인된 버전 JSON 로컬 다운로드 요청 · NAS 미검증");
  output({status:proof.status,manual_owner_review_required:proof.manual_owner_review_required,
          original_paths_included:false,external_transfer:false,nas_verified:false});
}));
el("meta-save").addEventListener("click", () => act(async () => {
  if (!workflow || workflow.template !== "required_file_metadata_v1" ||
      !review || !["LOCAL_METADATA_FINDINGS_READY", "LOCAL_METADATA_BLOCKED"].includes(review.status) ||
      !el("meta-save-consent").checked)
    throw Error("완료된 실제 로컬 점검·필수파일 계획·별도 저장 동의가 필요합니다.");
  const ticket = review;
  lastLocalReport = null;
  const wf = workflow.workflow_id;
  el("meta-save-consent").checked = false;
  review = null;  // Never replay a consent ticket after a lost reply.
  const saved = await json("/v1/workflows/" + wf + "/local-metadata", {
    review_id: ticket.review_id, scope_sha256: ticket.scope_sha256,
    acknowledgement: "SAVE_REDACTED_LOCAL_METADATA_RECEIPT"
  });
  if (saved.status !== "REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS")
    throw Error("로컬 증거 저장 응답 검증 실패");
  status("승인된 실제 로컬 메타데이터 결과를 SQLite에 저장 · NAS 실행 아님");
  output(saved);
}));
el("meta-readback").addEventListener("click", () => act(async () => {
  if (!workflow || workflow.template !== "required_file_metadata_v1")
    throw Error("필수 파일 워크플로를 먼저 선택해야 합니다.");
  const saved = await json("/v1/workflows/" + workflow.workflow_id + "/local-metadata");
  if (saved.status !== "REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS")
    throw Error("증거 검증 실패");
  status("SQLite 저장 증거 재조회 · 로컬 원본 재검사 없음");
  output(saved);
}));
el("meta-council").addEventListener("click", () => act(async () => {
  if (!workflow || workflow.template !== "required_file_metadata_v1")
    throw Error("필수 파일 워크플로만 검토할 수 있습니다.");
  const result = await json("/v1/workflows/" + workflow.workflow_id + "/local-council");
  if (result.schema !== "flowpilot-local-council-g230-v1" ||
      result.release_gate !== "HOLD" || result.real_nas_verified !== false ||
      result.independent_ai_council_invoked !== false)
    throw Error("로컬 검토 응답 검증 실패");
  lastLocalReport = null;
  status("기존 실측 로컬 메타데이터 4관점 정책 검토 · NAS 실행 없음");
  output(result);
}));
el("meta-report").addEventListener("click", () => act(async () => {
  if (!workflow || workflow.template !== "required_file_metadata_v1")
    throw Error("필수 파일 워크플로만 보고할 수 있습니다.");
  lastLocalReport = null;
  const result = await json("/v1/workflows/" + workflow.workflow_id + "/local-report");
  if (result.schema !== "flowpilot-local-operator-report-g230-v1" ||
      result.status !== "OWNER_LOCAL_REPORT_READY_NOT_NAS" ||
      result.release_gate !== "HOLD" || result.real_nas_verified !== false ||
      result.report_data_is_redacted !== true ||
      typeof result.report_markdown !== "string" || result.report_markdown.length > 6000)
    throw Error("로컬 보고서 응답 검증 실패");
  lastLocalReport = result;
  status("실측 로컬 메타데이터 기반 보고서 · NAS 검증 아님");
  output(result);
}));
el("native-handoff").addEventListener("click", () => act(async () => {
  if (!workflow || workflow.template !== "required_file_metadata_v1")
    throw Error("필수 파일 워크플로의 저장 증거가 필요합니다.");
  const result = await json("/v1/workflows/" + workflow.workflow_id + "/native-handoff");
  if (result.schema !== "flowpilot-g236-redacted-native-handoff-v1" ||
      result.status !== "NATIVE_EXECUTION_BLOCKED_PENDING_RUNTIME_EVIDENCE" ||
      result.workflow_id !== workflow.workflow_id ||
      result.release_gate !== "HOLD" || result.nas_verified !== false ||
      result.actual_registered_expert_invoked !== false ||
      result.live_nas_readback_verified !== false ||
      !Array.isArray(result.stages) || result.stages.length > 8)
    throw Error("Expert 연동 검토 응답 검증 실패");
  status("실제 로컬 증거 기반 Expert 연동 전 검토 · 실행 및 NAS 검증 없음");
  output(result);
}));
el("meta-export").addEventListener("click", () => act(async () => {
  if (!lastLocalReport || !workflow ||
      workflow.workflow_id !== lastLocalReport.workflow_id)
    throw Error("현재 워크플로의 확인된 로컬 보고서가 필요합니다.");
  const blob = new Blob([lastLocalReport.report_markdown], {type:"text/markdown;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = "flowpilot-local-evidence-not-nas.md";
  document.body.append(anchor); anchor.click(); anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status("로컬 증거 보고서 저장 요청 완료 · 개인 파일명 포함 안 함");
}));
// G240: allowlisted redacted-only export, independent of read approval.
function redactedCsvExport(receipt) {
  const r = receipt?.result, rows = r?.redacted_group_totals;
  const isInt = (n,max) => Number.isSafeInteger(n) && n >= 0 && n <= max;
  const isHash = s => typeof s === "string" && /^[0-9a-f]{64}$/.test(s);
  if (receipt?.schema !== "flowpilot-g239-local-csv-job-v1" ||
      receipt.status !== "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS" ||
      !/^csv_[0-9a-f]{24}$/.test(receipt.request_id || "") ||
      !isHash(receipt.plan_sha256) || receipt.path_and_labels_persisted !== false ||
      receipt.nas_verified !== false || receipt.release_gate !== "HOLD" ||
      r?.schema !== "flowpilot-g238-owner-local-typed-csv-v1" ||
      r.status !== "APPROVED_LOCAL_TYPED_WORKFLOW_COMPLETE_NOT_NAS" ||
      r.plan_sha256 !== receipt.plan_sha256 ||
      !isHash(r.source_sha256) || !isHash(r.report_sha256) ||
      !isHash(r.receipt_sha256) ||
      r.owner_source_modified !== false || r.raw_group_names_in_response !== false ||
      r.external_calls_performed !== false || r.nas_verified !== false ||
      typeof r.report_file_created !== "boolean" || r.local_audit_file_created !== false ||
      r.release_gate !== "HOLD" ||
      !isInt(r.source_rows,256) || !isInt(r.group_count,32) ||
      !Array.isArray(rows) || rows.length !== r.group_count ||
      !rows.every((v,i) => v && Object.keys(v).sort().join(",") ===
        "group_index,source_rows,total_cents" && v.group_index === i+1 &&
        isInt(v.total_cents,256000000) &&
        isInt(v.source_rows,256) && v.source_rows > 0) ||
      rows.reduce((sum,v) => sum+v.source_rows,0) !== r.source_rows)
    throw Error("익명화 CSV 영수증 구조/무결성 확인 실패");
  return {
    schema:"flowpilot-g240-redacted-csv-export-v1",
    status:"LOCAL_REDACTED_CSV_EXPORT_NOT_NAS",
    request_id:receipt.request_id,
    plan_sha256:receipt.plan_sha256,
    source_sha256:r.source_sha256,
    report_sha256_of_unexported_full_report:r.report_sha256,
    receipt_sha256:r.receipt_sha256,
    source_rows:r.source_rows,group_count:r.group_count,
    redacted_group_totals:rows.map(v => ({
      group_index:v.group_index,total_cents:v.total_cents,source_rows:v.source_rows
    })),
    raw_source_included:false,owner_path_included:false,
    group_labels_included:false,full_report_file_created_locally:r.report_file_created,
    nas_verified:false,release_gate:"HOLD"
  };
}
function randomCsvJobId() {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return "csv_" + Array.from(bytes, x => x.toString(16).padStart(2, "0")).join("");
}
// G242: capability-grounded intent mapping, NOT open-ended AI or NAS access.
// Exact phrases are deliberately narrow: unknown, compound or write/transfer
// intents fail closed. This stage never contacts the server or touches a CSV.
const CSV_INTENTS = Object.freeze({
  "고객별 매출 합계":"customer",
  "고객별 매출 집계":"customer",
  "고객별 매출 합계를 계산해줘":"customer",
  "부서별 매출 합계":"department",
  "부서별 매출 집계":"department",
  "부서별 매출 합계를 계산해줘":"department",
  "프로젝트별 매출 합계":"project",
  "프로젝트별 매출 집계":"project",
  "프로젝트별 매출 합계를 계산해줘":"project",
  "sum revenue by customer":"customer",
  "sum revenue by department":"department",
  "sum revenue by project":"project",
  "group revenue by customer":"customer",
  "group revenue by department":"department",
  "group revenue by project":"project"
});
el("csv-intent-apply").addEventListener("click", () => act(async () => {
  const raw = el("csv-intent").value;
  // Rejecting an intent must also revoke ANY previously reviewed local read.
  el("csv-intent").value = "";
  csvTicket = null; csvJobId = null; csvReceipt = null;
  csvBoundReportPath = null;
  el("csv-consent").checked = false;
  el("csv-export-consent").checked = false;
  el("csv-report-path").value = "";
  el("csv-report-consent").checked = false;
  el("csv-recover-id").value = "";
  el("csv-job-status").textContent = "자연어 검토 중 · 과거 CSV 승인 폐기";
  if (typeof raw !== "string" || raw.length > 96)
    throw Error("지원하지 않는 로컬 CSV 의도입니다.");
  const normalized = raw.trim().toLowerCase().replace(/\s+/g, " ");
  if (!Object.prototype.hasOwnProperty.call(CSV_INTENTS, normalized))
    throw Error("지원하지 않는 로컬 CSV 의도입니다.");
  const group = CSV_INTENTS[normalized];
  el("csv-group-column").value = group;
  el("csv-job-status").textContent = "승인된 의도: " + group +
    " · 아직 CSV 미조회 · SHA 계획 확인 및 별도 동의 필요 · NAS 아님";
  status("제한된 자연어를 코드 소유 4단계 CSV 작업으로 변환 · 읽기 전 계획 확인 필요");
  output({
    schema:"flowpilot-g242-csv-intent-v1",
    status:"TYPED_LOCAL_INTENT_ONLY_NO_READ",
    group_column:group,
    typed_nodes:["csv_read","validate_decimal","group_sum","report"],
    source_file_touched:false,
    consent_to_read:false,
    nas_verified:false,
    release_gate:"HOLD"
  });
}));
el("csv-verify-consent").addEventListener("change", sync);
el("csv-verify-path").addEventListener("input", sync);
el("csv-report-consent").addEventListener("change", sync);
el("csv-report-path").addEventListener("input", sync);
el("csv-consent").addEventListener("change", sync);
el("csv-export-consent").addEventListener("change", sync);
el("csv-preview").addEventListener("click", () => act(async () => {
  csvTicket = null; csvJobId = null; csvReceipt = null;
  csvBoundReportPath = null;
  el("csv-verify-path").value = "";
  el("csv-verify-consent").checked = false;
  el("csv-report-consent").checked = false;
  el("csv-consent").checked = false;
  el("csv-export-consent").checked = false;
  el("csv-recover-id").value = "";
  const inputPath = el("csv-local-path").value;
  const groupColumn = el("csv-group-column").value;
  const previewReportPath = el("csv-report-path").value;
  // Clear the raw private path from the DOM BEFORE any request, including errors.
  el("csv-local-path").value = "";
  el("csv-job-status").textContent = "새 CSV 계획 검토 중 · 이전 승인 폐기";
  if (!inputPath || inputPath.length > 1024 ||
      previewReportPath.length > 1024)
    throw Error("로컬 CSV 절대경로 및 보고서 대상 경로 확인 필요");
  const request = {input_path: inputPath, group_column: groupColumn};
  if (previewReportPath) request.export_to = previewReportPath;
  const p = await json("/v1/local-csv/preview", request);
  if (p.schema !== "flowpilot-g238-owner-local-typed-csv-v1" ||
      p.status !== "WAITING_EXPLICIT_LOCAL_CSV_JOB_APPROVAL" ||
      p.release_gate !== "HOLD" || p.real_nas_verified !== false ||
      p.input_file_touched !== false ||
      !/^cpre_[0-9a-f]{32}$/.test(p.preview_id) ||
      !/^[0-9a-f]{64}$/.test(p.plan_sha256) ||
      p.create_only_report_planned !== !!previewReportPath ||
      p.report_path_in_response !== false ||
      (previewReportPath ?
        !/^[0-9a-f]{64}$/.test(p.report_destination_sha256) :
        p.report_destination_sha256 !== null))
    throw Error("로컬 CSV 계획 검증 실패");
  csvTicket = p;
  csvBoundReportPath = previewReportPath;
  el("csv-job-status").textContent =
    "계획 SHA " + p.plan_sha256.slice(0, 16) +
    (p.create_only_report_planned ?
      " · 출력경로 SHA " + p.report_destination_sha256.slice(0, 16) : "") +
    " · 실행 전 별도 승인 필요";
  status("로컬 CSV 미리보기 완료 · 아직 파일을 읽지 않음 · NAS 아님");
  output(p);
}));
el("csv-run").addEventListener("click", () => act(async () => {
  if (!csvTicket || !el("csv-consent").checked)
    throw Error("현재 로컬 CSV 계획을 확인하고 동의해야 합니다.");
  const p = csvTicket;
  const boundPath = csvBoundReportPath;
  const reportPath = el("csv-report-path").value;
  const reportConsent = el("csv-report-consent").checked;
  // Revoke both permissions and private destination before any POST/failure.
  el("csv-report-path").value = "";
  el("csv-report-consent").checked = false;
  // One-shot client consent. Preserve ONLY the job ID after uncertain POST.
  csvTicket = null; csvReceipt = null;
  csvBoundReportPath = null;
  el("csv-verify-path").value = "";
  el("csv-verify-consent").checked = false;
  if (boundPath === null || reportPath !== boundPath ||
      p.create_only_report_planned !== reportConsent ||
      (!!reportPath) !== reportConsent ||
      (reportConsent && reportPath.length > 1024))
    throw Error("새 로컬 CSV 저장 경로와 독립 승인 둘 다 필요합니다.");
  el("csv-consent").checked = false;
  el("csv-export-consent").checked = false;
  const job = randomCsvJobId();
  csvJobId = job;
  el("csv-job-status").textContent = "실행 결과 미확인 · 작업 ID " + job + " · 영수증 GET 재조회 가능 · 자동 재시도 금지";
  const request = {
    preview_id: p.preview_id, request_id: job,
    plan_sha256: p.plan_sha256, acknowledgement: "APPROVE_LOCAL_CSV_READ_ONCE"
  };
  if (reportConsent) {
    request.export_to = reportPath;
    request.export_approval = "APPROVE_LOCAL_REPORT_CREATE";
  }
  const result = await json("/v1/local-csv/run", request);
  if (result.schema !== "flowpilot-g239-local-csv-job-v1" ||
      result.request_id !== job ||
      result.status !== "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS" ||
      result.plan_sha256 !== p.plan_sha256 ||
      result.release_gate !== "HOLD" || result.nas_verified !== false ||
      result.path_and_labels_persisted !== false ||
      result.result?.nas_verified !== false ||
      result.result?.report_file_created !== reportConsent)
    throw Error("CSV 실행 영수증 검증 실패");
  redactedCsvExport(result);
  csvReceipt = result;
  el("csv-job-status").textContent = "로컬 CSV 완료 · 영수증 " + job + " · NAS 미검증";
  status(reportConsent ? "로컬 CSV 집계 및 별도 승인한 새 보고서 파일 생성 · 원본 불변" :
    "로컬 CSV 실제 집계 완료 · 원본 수정/외부 전송 없음");
  output(result);
}));
async function readCsvJob(id) {
  el("csv-verify-path").value = "";
  el("csv-verify-consent").checked = false;
  if (typeof id !== "string" || !/^csv_[0-9a-f]{24}$/.test(id))
    throw Error("복구할 CSV 작업 ID가 올바르지 않습니다.");
  // Revoke old export rights before an uncertain GET, not after it.
  csvReceipt = null;
  el("csv-export-consent").checked = false;
  const result = await json("/v1/local-csv/jobs/" + id);
  if (result.schema !== "flowpilot-g239-local-csv-job-v1" ||
      result.request_id !== id ||
      result.release_gate !== "HOLD" || result.nas_verified !== false ||
      !["COMPLETE_LOCAL_TYPED_CSV_NOT_NAS",
        "RUN_RESERVED_UNCERTAIN_NO_AUTORETRY",
        "LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY"].includes(result.status))
    throw Error("CSV 저장 영수증 검증 실패");
  if (result.status === "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS") {
    redactedCsvExport(result);
    csvReceipt = result;
  }
  el("csv-job-status").textContent = result.status + " · " + id + " · NAS 미검증";
  status("SQLite 저장 영수증 재조회 · 고객 CSV 다시 읽지 않음");
  output(result);
}
el("csv-readback").addEventListener("click", () => act(async () => {
  if (!csvJobId) throw Error("먼저 CSV 작업을 선택해야 합니다.");
  await readCsvJob(csvJobId);
}));
el("csv-recover").addEventListener("click", () => act(async () => {
  const id = el("csv-recover-id").value;
  // No storage or implicit rerun; an operator must enter a recorded job ID.
  el("csv-recover-id").value = "";
  csvTicket = null; csvJobId = null; csvReceipt = null;
  el("csv-consent").checked = false;
  el("csv-export-consent").checked = false;
  el("csv-report-path").value = "";
  el("csv-report-consent").checked = false;
  if (!/^csv_[0-9a-f]{24}$/.test(id))
    throw Error("복구할 CSV 작업 ID가 올바르지 않습니다.");
  csvJobId = id;
  await readCsvJob(id);
}));
// G243 explicitly consented, authenticated, read-only history of at most 10
// approved local receipt IDs. No source CSV open, no export consent inheritance.
el("csv-history-consent").addEventListener("change", sync);
el("csv-history-select").addEventListener("change", sync);
el("csv-history-list").addEventListener("click", () => act(async () => {
  if (!el("csv-history-consent").checked)
    throw Error("별도 로컬 영수증 목록 조회 동의가 필요합니다.");
  el("csv-history-consent").checked = false;
  el("csv-history-select").replaceChildren(new Option("선택 안 함", ""));
  csvReceipt = null;
  el("csv-export-consent").checked = false;
  const result = await json("/v1/local-csv/jobs", undefined, true);
  const allowed = new Set([
    "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS",
    "RUN_RESERVED_UNCERTAIN_NO_AUTORETRY",
    "LOCAL_CSV_RUN_BLOCKED_NO_AUTORETRY"
  ]);
  if (result.schema !== "flowpilot-g243-csv-history-v1" ||
      result.status !== "LOCAL_CSV_HISTORY_NOT_NAS" ||
      result.release_gate !== "HOLD" || result.nas_verified !== false ||
      result.source_files_accessed !== false || result.read_only !== true ||
      result.max_returned !== 10 || !Array.isArray(result.jobs) ||
      result.jobs.length > 10 || result.count !== result.jobs.length ||
      !result.jobs.every(x =>
        x && /^csv_[0-9a-f]{24}$/.test(x.request_id) &&
        allowed.has(x.status) &&
        Object.keys(x).every(key => ["request_id","status","group_count","source_rows"].includes(key)) &&
        (x.status === "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS"
          ? Number.isSafeInteger(x.group_count) && x.group_count >= 1 && x.group_count <= 32 &&
            Number.isSafeInteger(x.source_rows) && x.source_rows >= x.group_count && x.source_rows <= 256
          : x.group_count === undefined && x.source_rows === undefined)))
    throw Error("검증되지 않은 CSV 영수증 목록 응답");
  for (const item of result.jobs) {
    const title = item.status + " · " + item.request_id.slice(-6) +
      (item.source_rows ? " · " + item.source_rows + "행" : "");
    el("csv-history-select").add(new Option(title,item.request_id));
  }
  status("조회 승인 1회 소비 · 최근 영수증 번호만 확인 · 고객 CSV 미조회");
  output(result);
}));
el("csv-history-open").addEventListener("click", () => act(async () => {
  const id = el("csv-history-select").value;
  if (!/^csv_[0-9a-f]{24}$/.test(id) ||
      ![...el("csv-history-select").options].some(x => x.value === id))
    throw Error("검증된 로컬 CSV 목록 항목을 선택해야 합니다.");
  csvTicket = null; csvJobId = id; csvReceipt = null;
  el("csv-report-path").value = "";
  el("csv-report-consent").checked = false;
  el("csv-consent").checked = false;
  el("csv-export-consent").checked = false;
  await readCsvJob(id); // no run POST
}));
// G245 separate one-shot LOCAL file inspection; no input CSV reread or
// persisted path, and a digest mismatch must never be displayed as a success.
el("csv-verify-report").addEventListener("click", () => act(async () => {
  const receipt = csvReceipt;
  const file = el("csv-verify-path").value;
  const authorized = el("csv-verify-consent").checked;
  el("csv-verify-path").value = "";
  el("csv-verify-consent").checked = false;
  el("csv-export-consent").checked = false;
  if (!authorized || !file || file.length > 1024 ||
      receipt?.status !== "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS" ||
      receipt?.result?.report_file_created !== true ||
      !/^csv_[0-9a-f]{24}$/.test(receipt?.request_id || ""))
    throw Error("로컬 생성 보고서의 영수증·경로·별도 읽기 동의 필요");
  const result = await json("/v1/local-csv/verify-report", {
    request_id:receipt.request_id,report_path:file,
    acknowledgement:"APPROVE_LOCAL_REPORT_VERIFY_ONCE"
  });
  const verified = result?.status === "VERIFIED_LOCAL_OUTPUT_SHA_NOT_NAS";
  const conflict = result?.status === "CONFLICT_LOCAL_OUTPUT_SHA_NOT_NAS";
  if (result?.schema !== "flowpilot-g245-local-output-verify-v1" ||
      (!verified && !conflict) || result.request_id !== receipt.request_id ||
      result.release_gate !== "HOLD" || result.nas_verified !== false ||
      result.matches_recorded_receipt !== verified ||
      result.local_output_read_once !== true ||
      result.original_input_reopened !== false ||
      result.execution_replayed !== false ||
      result.private_path_or_labels_included !== false ||
      result.sqlite_mutated !== false ||
      !/^[0-9a-f]{64}$/.test(result.expected_report_sha256 || "") ||
      result.expected_report_sha256 !== receipt.result.report_sha256 ||
      !/^[0-9a-f]{64}$/.test(result.observed_report_sha256 || ""))
    throw Error("로컬 생성 보고서 검증 응답 무결성 실패");
  status(verified ?
    "로컬 생성 CSV SHA-256 일치 · NAS 미검증" :
    "로컬 생성 CSV SHA-256 불일치 · 사용 전 수동 확인 필요");
  output(result);
}));
el("csv-export").addEventListener("click", () => act(async () => {
  if (!csvReceipt || !el("csv-export-consent").checked)
    throw Error("검증한 CSV 영수증과 별도 다운로드 동의가 필요합니다.");
  el("csv-export-consent").checked = false;
  const data = redactedCsvExport(csvReceipt);
  const blob = new Blob([JSON.stringify(data,null,2) + "\n"],
    {type:"application/json;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "flowpilot-local-redacted-csv-not-nas.json";
  document.body.append(anchor);anchor.click();anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url),1000);
  status("별도 승인한 익명화 CSV 영수증 다운로드 · 원본/그룹명 미포함");
}));
// Existing G117 advisor: only user-provided numeric samples, never a NAS watcher.
el("advice-submit").addEventListener("click", () => act(async () => {
  if (!el("advice-consent").checked)
    throw Error("일회성 수치 분석에 별도 동의가 필요합니다.");
  const values = adviceFields.map(([id, key, upper]) =>
    ({key, value:el(id).value, upper}));
  // Revoke this one-use consent and wipe inputs before validation/network I/O.
  clearAdvice();
  const telemetry = {};
  for (const {key, value, upper} of values) {
    if (value === "") continue;
    if (!/^[0-9]+$/.test(value) || Number(value) > upper)
      throw Error("수치 입력은 범위 내 정수만 허용합니다.");
    telemetry[key] = Number(value);
  }
  if (!Object.keys(telemetry).length)
    throw Error("수치 최소 1개가 필요합니다.");
  el("advice-summary").textContent = "일회성 분석 요청 · 재사용 동의 없음";
  const result = await json("/v1/advice", {telemetry, opt_in:true});
  const codes = {
    REVIEW_DISK_CAPACITY:"디스크 용량 검토",
    REVIEW_REPEATED_ERRORS:"반복 오류 로그 검토",
    REVIEW_BACKUP_FRESHNESS:"백업 주기 검토"
  };
  const allowed = ["disk_used_percent","repeated_error_count","backup_age_hours"];
  const suggestionIds = result.suggestions?.map(s => s.id);
  if (result.schema !== "flowpilot-proactive-suggestions-v1" ||
      !["SUGGESTIONS_READY","NO_ALERTS_IN_SUPPLIED_DATA"].includes(result.status) ||
      result.source !== "UNVERIFIED_OPERATOR_SUPPLIED_METRICS" ||
      result.nas_polled !== false || result.telemetry_verified !== false ||
      result.actions_executed !== false || result.background_service_started !== false ||
      result.external_notifications_sent !== false || result.release_gate !== "HOLD" ||
      !Array.isArray(result.suggestions) || result.suggestions.length > 3 ||
      result.suggestion_count !== result.suggestions.length ||
      !Array.isArray(result.evaluated_fields) ||
      result.evaluated_fields.length !== Object.keys(telemetry).length ||
      !result.evaluated_fields.every(key => allowed.includes(key) &&
        Object.prototype.hasOwnProperty.call(telemetry, key)) ||
      !Array.isArray(result.missing_inputs_not_checked) ||
      result.missing_inputs_not_checked.length !== 3 - result.evaluated_fields.length ||
      !result.missing_inputs_not_checked.every(key => allowed.includes(key) &&
        !Object.prototype.hasOwnProperty.call(telemetry, key)) ||
      !suggestionIds.every(id => Object.prototype.hasOwnProperty.call(codes,id)) ||
      new Set(suggestionIds).size !== suggestionIds.length ||
      !result.suggestions.every(s => s.status === "PROPOSAL_ONLY" &&
        s.requires_explicit_user_approval_to_act === true &&
        s.verified_on_real_nas === false) ||
      (result.status === "SUGGESTIONS_READY") !== (result.suggestions.length > 0))
    throw Error("일회성 제안 응답 검증 실패");
  const message = result.suggestions.length ?
    "사람의 검토가 필요한 제안 " + result.suggestions.length + "개" :
    "입력된 수치에서 제안 조건 미검출";
  el("advice-summary").textContent = message + " · 미입력 미확인 " +
    result.missing_inputs_not_checked.length + "개 · 동의 재사용 불가";
  const lines = [
    "FlowPilot · 일회성 수동 입력 상태 제안",
    "원본 출처: 사용자 수동 입력 · 실제 NAS 수집/검증 없음",
    "로컬 상태: " + result.status,
    "제안 건수: " + result.suggestion_count,
    "미입력 항목: " + result.missing_inputs_not_checked.length + "개 (NOT_CHECKED)",
    ...result.suggestions.map((s,i) => (i + 1) + ". " + codes[s.id] +
      " · 사람 검토 필요 · 자동 조치 없음"),
    "외부 알림 0건 · 자동 수정 0건 · RELEASE HOLD"
  ];
  status("일회성 제안 검증 완료 · 실제 NAS 감시 아님"); output(lines.join("\n"));
}));
el("synthetic-consent").addEventListener("change", sync);
el("advice-consent").addEventListener("change", sync);
for (const [id] of adviceFields) el(id).addEventListener("input", sync);
el("metadata-goal").addEventListener("change", () => {
  // A different intent cannot inherit an already previewed scope or consent.
  review = null;
  lastLocalReport = null;
  el("metadata-consent").checked = false;
  el("meta-save-consent").checked = false;
  revokeVersionExport();
  el("required").value = "";
  el("version-candidates").value = "";
  el("text-workflow").value = "";
  el("version-intent").value = "";
  status("점검 의도 변경 · 기존 미리보기 및 읽기 승인 폐기");
  sync();
});
el("metadata-consent").addEventListener("change", sync);
el("meta-save-consent").addEventListener("change", sync);
el("version-export-consent").addEventListener("change", sync);
el("existing").addEventListener("change", sync);
el("clear").addEventListener("click", () => { output("화면 로그 초기화"); status("대기"); });
window.addEventListener("pagehide", () => { token = ""; el("version-intent").value = ""; revokeVersionExport(); clearAdvice(); });
sync();
