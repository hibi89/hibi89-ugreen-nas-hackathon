"use strict";
// G166: browser state is intentionally ephemeral. No cookies, storage or token in URLs.
const el = id => document.getElementById(id);
const controls = [...document.querySelectorAll("button")];
let token = "", workflow = null, verifiedPlan = null, review = null, busy = false;
function status(message) { el("notice").textContent = message; }
function output(data) { el("output").textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2); }
function sync() {
  el("workflow-id").textContent = workflow?.workflow_id || "없음";
  el("workflow-state").textContent = workflow?.status || "미생성";
  el("plan-hash").textContent = verifiedPlan ? "검증한 계획 SHA-256: " + verifiedPlan :
    "계획 SHA-256: 미확인";
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
      load: !!el("existing").value, plan: !!workflow,
      test: s === "PLANNED", approve: s === "TESTED" && !!verifiedPlan && el("synthetic-consent").checked,
      run: s === "APPROVED_SYNTHETIC", audit: !!workflow,
      evidence: s === "COMPLETE_LOCAL_SYNTHETIC", report: s === "COMPLETE_LOCAL_SYNTHETIC",
      recover: s === "RUNNING", "meta-approve": review?.status === "WAITING_APPROVAL" && el("metadata-consent").checked,
      "meta-cancel": review?.status === "WAITING_APPROVAL", "meta-status": !!review
    };
    button.disabled = Object.prototype.hasOwnProperty.call(rules, button.id) && !rules[button.id];
  }
}
async function api(path, body) {
  if (!token) throw Error("로컬 API 연결이 필요합니다.");
  const headers = { "Authorization": "Bearer " + token };
  if (body !== undefined) headers["Content-Type"] = "application/json";
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
async function json(path, body) { return (await api(path, body)).json(); }
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
  el("synthetic-consent").checked = false;
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
  token = ""; workflow = null; verifiedPlan = null; review = null;
  el("token").value = ""; el("required").value = "";
  el("synthetic-consent").checked = false; el("metadata-consent").checked = false;
  el("connection-status").textContent = "연결 해제 · 토큰 폐기";
  status("로컬 세션 연결 해제"); output("토큰은 저장되지 않습니다."); sync();
});
el("create").addEventListener("click", () => act(async () => {
  const result = await json("/v1/workflows", {goal: el("goal").value, request_id: randomRequestId()});
  resetWorkflow(result); status("합성 계획 생성 · 명시적 테스트와 승인 필요"); output(result);
}));
el("list").addEventListener("click", () => act(async () => {
  const result = await json("/v1/workflows");
  const select = el("existing");
  select.replaceChildren(new Option("선택 안 함", ""));
  for (const id of result.workflows) select.add(new Option(id, id));
  status("로컬 워크플로 조회 완료"); output(result);
}));
el("load").addEventListener("click", () => act(async () => {
  const id = el("existing").value;
  if (!/^wf_[0-9a-f]{32}$/.test(id)) throw Error("워크플로 ID를 선택하세요.");
  resetWorkflow(await json("/v1/workflows/" + id));
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
el("test").addEventListener("click", () => act(async () => {
  resetWorkflow(await json("/v1/workflows/" + workflow.workflow_id + "/test", {}));
  status("4역할 합성 테스트 완료 · 다시 계획 해시 확인 필요"); output(workflow);
}));
el("approve").addEventListener("click", () => act(async () => {
  if (workflow?.status !== "TESTED" || verifiedPlan !== workflow.plan_sha256 ||
      !el("synthetic-consent").checked) throw Error("TESTED · 해시 확인 · 명시적 동의가 필요합니다.");
  const hash = verifiedPlan;
  resetWorkflow(await json("/v1/workflows/" + workflow.workflow_id + "/approve", {
    plan_sha256: hash, acknowledgement: "APPROVE_SYNTHETIC_ONLY"
  }));
  status("합성 실행만 승인됨 · NAS 접근 미승인"); output(workflow);
}));
el("run").addEventListener("click", () => act(async () => {
  if (workflow?.status !== "APPROVED_SYNTHETIC") throw Error("승인된 합성 실행만 가능합니다.");
  resetWorkflow(await json("/v1/workflows/" + workflow.workflow_id + "/run", {}));
  status("로컬 합성 실행 완료 · 증거와 CSV를 개별 확인하세요."); output(workflow);
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
el("meta-preview").addEventListener("click", () => act(async () => {
  const required = el("required").value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
  if (required.length < 1 || required.length > 20) throw Error("경로 1–20개가 필요합니다.");
  review = await json("/v1/local-metadata/preview", {goal:"check required files",required});
  el("required").value = ""; el("metadata-consent").checked = false;
  status("로컬 메타데이터 읽기 전 미리보기 · 아직 파일 미조회"); output(review);
}));
el("meta-approve").addEventListener("click", () => act(async () => {
  if (!review || review.status !== "WAITING_APPROVAL" || !el("metadata-consent").checked)
    throw Error("검토 및 별도 동의가 필요합니다.");
  review = await json("/v1/local-metadata/approve", {
    review_id:review.review_id, scope_sha256:review.scope_sha256,
    acknowledgement:"APPROVE_LOCAL_METADATA_READ_ONLY"
  });
  el("metadata-consent").checked = false;
  status("로컬 메타데이터 1회 읽기 종료 · NAS 검증 아님"); output(review);
}));
el("meta-cancel").addEventListener("click", () => act(async () => {
  if (!review || review.status !== "WAITING_APPROVAL") throw Error("취소 가능한 검토 없음");
  review = await json("/v1/local-metadata/cancel", {review_id:review.review_id});
  el("metadata-consent").checked = false; status("검토 취소 · 메타데이터 읽기 없음"); output(review);
}));
el("meta-status").addEventListener("click", () => act(async () => {
  if (!review) throw Error("검토 세션 없음");
  review = await json("/v1/local-metadata/reviews/" + review.review_id);
  status("저장된 메모리 내 메타데이터 상태 재조회 · 재실행 없음"); output(review);
}));
el("synthetic-consent").addEventListener("change", sync);
el("metadata-consent").addEventListener("change", sync);
el("existing").addEventListener("change", sync);
el("clear").addEventListener("click", () => { output("화면 로그 초기화"); status("대기"); });
window.addEventListener("pagehide", () => { token = ""; });
sync();
