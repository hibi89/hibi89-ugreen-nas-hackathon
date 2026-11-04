"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const {webcrypto} = require("node:crypto");
const base = process.argv[2];
const auth = process.argv[3];
if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base) || !auth || auth.length < 32) {
  throw Error("local smoke parameters missing");
}
// Modern Node exposes crypto as a read-only global getter; retain its native WebCrypto.
if (!globalThis.crypto?.subtle) {
  Object.defineProperty(globalThis, "crypto", {value: webcrypto, configurable: true});
}
const nativeFetch = globalThis.fetch;
let rejectOneRunReply = false;
let runRequestCount = 0;
let readbackCount = 0;
let rejectOneCsvRunReply=false, csvRunPostCount=0, csvGetCount=0, csvHistoryGetCount=0, csvVerifyPostCount=0;
let rejectOneMetadataApproval = false;
let rejectOneMetadataCancel = false;
let adviceCalls = 0;
globalThis.fetch = (route, init) => {
  if (route === "/v1/local-csv/run") {
    csvRunPostCount++;
    if (rejectOneCsvRunReply) {
      rejectOneCsvRunReply=false;
      return nativeFetch(base+route,init).then(() => new Response(
        JSON.stringify({error:"SIMULATED_LOST_CSV_RESPONSE"}),
        {status:503,headers:{"Content-Type":"application/json"}}));
    }
  }
  if (route.startsWith("/v1/local-csv/jobs/")) csvGetCount++;
  if (route === "/v1/local-csv/jobs") csvHistoryGetCount++;
  if (route === "/v1/local-csv/verify-report") csvVerifyPostCount++;
  if (route.endsWith("/run") && route.startsWith("/v1/workflows/wf_")) {
    runRequestCount++;
    if (rejectOneRunReply) {
      rejectOneRunReply = false;
      // The real HTTP POST reaches SQLite and commits, but the client sees
      // an artificial HTTP 503 instead of the successful response.
      return nativeFetch(base + route, init).then(() =>
        new Response(JSON.stringify({error:"SIMULATED_LOST_RUN_REPLY"}), {
          status:503, headers:{"Content-Type":"application/json"}
        }));
    }
  }
  if (route.startsWith("/v1/workflows/wf_") &&
      !route.includes("/plan") && !route.includes("/guide") &&
      !route.includes("/audit") && !route.includes("/evidence") &&
      !route.includes("/report") && !route.endsWith("/run") &&
      !route.endsWith("/recover") && !route.endsWith("/test") &&
      !route.endsWith("/approve")) readbackCount++;
  if (route === "/v1/local-metadata/approve" && rejectOneMetadataApproval) {
    rejectOneMetadataApproval = false;
    return Promise.resolve(new Response(JSON.stringify({error:"SIMULATED_HTTP_503"}), {
      status:503, headers:{"Content-Type":"application/json"}
    }));
  }
  if (route === "/v1/local-metadata/cancel" && rejectOneMetadataCancel) {
    rejectOneMetadataCancel = false;
    return Promise.resolve(new Response(JSON.stringify({error:"SIMULATED_CANCEL_TIMEOUT"}), {
      status:503, headers:{"Content-Type":"application/json"}
    }));
  }
  if (route === "/v1/advice") adviceCalls++;
  return nativeFetch(base + route, init);
};
const ids = ["token","connect","disconnect","clear","connection-status","notice","output",
  "workflow-id","workflow-state","plan-hash","metadata-summary","goal","existing","create",
  "list","load","plan","guide","test","approve","run","refresh","audit","evidence","report","recover",
  "synthetic-consent","metadata-consent","required","version-candidates","metadata-goal","text-workflow","text-preview","meta-preview","meta-approve",
  "meta-cancel","meta-status","version-export","meta-save","meta-readback","meta-council","meta-report","meta-export","native-handoff","local-council-state","meta-save-consent","version-export-consent","advice-disk","advice-errors","advice-backup",
  "advice-consent","advice-submit","advice-summary","csv-local-path","csv-group-column","csv-preview","csv-run","csv-readback","csv-consent","csv-job-status","csv-export-consent","csv-export","csv-recover-id","csv-recover","csv-intent","csv-intent-apply","csv-report-path","csv-report-consent","csv-verify-path","csv-verify-consent","csv-verify-report","csv-history-consent","csv-history-select","csv-history-list","csv-history-open"];
const buttonIds = ["connect","disconnect","clear","create","list","load","plan","guide",
  "test","approve","run","refresh","audit","evidence","report","recover","text-preview","meta-preview",
  "meta-approve","meta-cancel","meta-status","version-export","meta-save","meta-readback","meta-council","meta-report","meta-export","native-handoff","advice-submit","csv-preview","csv-run","csv-readback","csv-export","csv-recover","csv-intent-apply","csv-history-list","csv-history-open","csv-verify-report"];
class FakeElement {
  constructor(id) {this.id=id;this.value="";this.checked=false;this.disabled=false;
    this.textContent="";this.handlers={};this.options=[];}
  addEventListener(name,fn) {this.handlers[name]=fn;}
  fire(name="click") {assert(this.handlers[name],this.id + " lacks handler");
    assert.equal(this.disabled,false,this.id + " disabled");return this.handlers[name]();}
  replaceChildren(...items) {this.options=[...items];this.value="";}
  add(item) {this.options.push(item);}
  remove() {}
  click() {globalThis.__downloads=(globalThis.__downloads||0)+1;}
}
const elems=Object.fromEntries(ids.map(id=>[id,new FakeElement(id)]));
elems.goal.value="check required files";
elems["metadata-goal"].value="check required files";
globalThis.Option=function(label,value){return {label,value};};
globalThis.document={
  getElementById:id=>{if(!elems[id])throw Error("Missing DOM element "+id);return elems[id];},
  querySelectorAll:query=>{assert.equal(query,"button");return buttonIds.map(id=>elems[id]);},
  createElement:name=>{assert.equal(name,"a");return new FakeElement("download-anchor");},
  body:{append(){}}
};
globalThis.window={addEventListener(name,fn){assert.equal(name,"pagehide");}};
const source=fs.readFileSync(path.join(__dirname,"../tools/flowpilot_g166_dashboard.js"),"utf8");
require("node:vm").runInThisContext(source,{filename:"flowpilot_g166_dashboard.js"});
async function click(id) {await elems[id].fire();}
async function main(){
  assert.equal(elems.create.disabled,true,"must not create without local auth");
  assert.equal(elems["csv-preview"].disabled,true,"CSV plan needs local authentication");
  elems.token.value=auth;
  await click("connect");
  assert.equal(elems.token.value,"","token must clear from password DOM");
  assert.match(elems["connection-status"].textContent,/연결 확인/);
  // Explicit, single-use opt-in; invalid values never hit the server.
  assert.equal(elems["advice-submit"].disabled,true,"no unsolicited telemetry request");
  elems["advice-disk"].value="95"; elems["advice-disk"].fire("input");
  assert.equal(elems["advice-submit"].disabled,true,"numeric sample alone is not consent");
  elems["advice-errors"].value="3";
  elems["advice-backup"].value="73";
  elems["advice-consent"].checked=true;elems["advice-consent"].fire("change");
  await click("advice-submit");
  assert.equal(adviceCalls,1,"one consent = one request");
  assert.match(elems.output.textContent,/제안 건수: 3/);
  assert.match(elems.output.textContent,/디스크 용량 검토/);
  assert.match(elems.output.textContent,/반복 오류 로그 검토/);
  assert.match(elems.output.textContent,/백업 주기 검토/);
  assert.match(elems.output.textContent,/실제 NAS 수집\/검증 없음/);
  assert.equal(elems["advice-disk"].value,"");
  assert.equal(elems["advice-errors"].value,"");
  assert.equal(elems["advice-backup"].value,"");
  assert.equal(elems["advice-consent"].checked,false);
  assert.equal(elems["advice-submit"].disabled,true);
  elems["advice-disk"].value="20";elems["advice-disk"].fire("input");
  elems["advice-consent"].checked=true;elems["advice-consent"].fire("change");
  await click("advice-submit");
  assert.equal(adviceCalls,2);
  assert.match(elems.output.textContent,/NO_ALERTS_IN_SUPPLIED_DATA/);
  assert.match(elems.output.textContent,/미입력 항목: 2개/);
  elems["advice-disk"].value="101";elems["advice-disk"].fire("input");
  elems["advice-consent"].checked=true;elems["advice-consent"].fire("change");
  await click("advice-submit");
  assert.equal(adviceCalls,2,"invalid metric refused before network send");
  assert.equal(elems["advice-disk"].value,"");
  assert.equal(elems["advice-consent"].checked,false);
  assert.match(elems.notice.textContent,/요청 거부/);
  await click("create");
  assert.match(elems["workflow-id"].textContent,/^wf_[0-9a-f]{32}$/);
  const workflowId=elems["workflow-id"].textContent;
  assert.equal(elems.guide.disabled,false,"guide requires a workflow");
  await click("guide");
  assert.match(elems.output.textContent,/합성 전용 7단계 운영 가이드/);
  assert.match(elems.output.textContent,/현재 실행 상태: PLANNED/);
  assert.match(elems.output.textContent,/로컬 검증 단계: 2\/6/);
  assert.match(elems.output.textContent,/3\. \[NEXT\] 4역할 합성 검증/);
  assert.match(elems.output.textContent,/브라우저 대조 완료/);
  assert.match(elems.output.textContent,/7\. \[OFFICIAL_BLOCKED\] 운영 전 승인 게이트/);
  assert.doesNotMatch(elems.output.textContent,/FLOWPILOT_LOCAL_API_TOKEN|Bearer /);
  assert.equal(elems.approve.disabled,true,"cannot approve before council test");
  await click("plan");
  assert.match(elems["plan-hash"].textContent,/[a-f0-9]{64}/);
  await click("test");
  assert.equal(elems["workflow-state"].textContent,"TESTED");
  assert.equal(elems.approve.disabled,true,"needs fresh hash and consent");
  await click("plan");
  assert.equal(elems.approve.disabled,true,"needs consent");
  elems["synthetic-consent"].checked=true;elems["synthetic-consent"].fire("change");
  assert.equal(elems.approve.disabled,false);
  await click("approve");
  assert.equal(elems["workflow-state"].textContent,"APPROVED_SYNTHETIC");
  // Run-response-loss after the actual local backend committed must not
  // leave an enabled re-execution button or silently resubmit.
  rejectOneRunReply = true;
  await click("run");
  assert.equal(runRequestCount,1,"only one synthetic run POST");
  assert.equal(elems.run.disabled,true,"ambiguous result cannot rerun");
  assert.equal(elems.refresh.disabled,false,"safe GET status reconciliation available");
  assert.match(elems["workflow-state"].textContent,/결과 미확인/);
  assert.equal(elems["synthetic-consent"].checked,false);
  assert.match(elems.notice.textContent,/요청 거부|연결 오류/);
  const beforeReadback = readbackCount;
  await click("refresh");
  assert.equal(readbackCount,beforeReadback+1,"one read-only status GET");
  assert.equal(runRequestCount,1,"readback never repeats run POST");
  assert.equal(elems["workflow-state"].textContent,"COMPLETE_LOCAL_SYNTHETIC");
  assert.match(elems.notice.textContent,/실행 재요청 없음/);
  assert.equal(elems.run.disabled,true);
  await click("guide");
  assert.match(elems.output.textContent,/현재 실행 상태: COMPLETE_LOCAL_SYNTHETIC/);
  assert.match(elems.output.textContent,/로컬 검증 단계: 6\/6/);
  assert.match(elems.output.textContent,/6\. \[VERIFIED_LOCAL\] 감사·산출물/);
  assert.match(elems.output.textContent,/7\. \[OFFICIAL_BLOCKED\] 운영 전 승인 게이트/);
  await click("audit");assert.match(elems.output.textContent,/LOCAL_CHAIN_INTACT/);
  await click("evidence");assert.match(elems.output.textContent,/NOT_NAS/);
  await click("report");
  assert.equal(globalThis.__downloads,1,"one authenticated CSV download after digest verified");
  assert.match(elems.output.textContent,/LOCAL_SYNTHETIC_CSV_SHA_VERIFIED/);
  await click("list");
  const saved = elems.existing.options.find(x=>x.value===workflowId);
  assert(saved,"workflow listed from SQLite");
  assert.match(saved.label,/필수 파일 점검 \(합성\)/,"stored type is shown");
  assert.match(saved.label,/COMPLETE_LOCAL_SYNTHETIC/,"stored status is shown");
  assert.match(saved.label,new RegExp(workflowId.slice(-6)+"$"),"opaque ID is shortened");
  assert(!saved.label.includes("check required files"),"raw user goal is never shown");
  elems.existing.value=workflowId;elems.existing.fire("change");
  await click("load");assert.equal(elems["workflow-state"].textContent,"COMPLETE_LOCAL_SYNTHETIC");
  // G248 exact version-review goal is an independently approvable typed,
  // read-only local workflow, not a silently persisted synthetic runner.
  elems["metadata-goal"].value="review versions";elems["metadata-goal"].fire("change");
  assert.equal(elems["meta-approve"].disabled,true);
  elems.required.value="README.md";
  await click("meta-preview");
  assert.match(elems.notice.textContent,/요청 거부|연결 오류/);
  assert.equal(elems["meta-approve"].disabled,true);
  elems.required.value="README.md";
  elems["version-candidates"].value="README.md=not-a-version.pdf";
  await click("meta-preview");
  const versionPreview=JSON.parse(elems.output.textContent);
  assert.equal(versionPreview.selected_intent,"REVIEW_VERSIONS");
  assert.equal(versionPreview.typed_review_plan.length,4);
  assert.equal(versionPreview.approved_local_metadata_access,false);
  assert.equal(elems["version-export"].disabled,true,"no export before read opt-in");
  assert.equal(elems["metadata-consent"].checked,false);
  assert.equal(elems["meta-approve"].disabled,true);
  elems["metadata-consent"].checked=true;elems["metadata-consent"].fire("change");
  assert.equal(elems["meta-approve"].disabled,false);
  await click("meta-approve");
  const versionResult=JSON.parse(elems.output.textContent);
  assert.equal(versionResult.selected_intent,"REVIEW_VERSIONS");
  assert.equal(versionResult.nas_verified,false);
  assert.equal(versionResult.file_contents_opened,false);
  assert.equal(elems["version-export"].disabled,true,"second consent required");
  elems["version-export-consent"].checked=true;
  elems["version-export-consent"].fire("change");
  const createUrlOld=URL.createObjectURL;let versionBlob=null;
  URL.createObjectURL=function(blob){versionBlob=blob;return createUrlOld.call(URL,blob);};
  try { await click("version-export"); } finally { URL.createObjectURL=createUrlOld; }
  const doc=JSON.parse(await versionBlob.text());
  assert.equal(doc.schema,"flowpilot-local-version-evidence-g249-v1");
  assert.equal(doc.nas_verified,false);
  assert.equal(doc.owner_paths_included,false);
  assert.equal(doc.auto_selected_final_version,false);
  assert.equal(doc.findings.length,1);
  assert(!JSON.stringify(doc).includes("README.md"));
  assert(!JSON.stringify(doc).includes("not-a-version.pdf"));
  assert.equal(elems["version-export-consent"].checked,false);
  assert.equal(elems["version-export"].disabled,true,"one opt-in per download");
  assert.equal(elems["metadata-consent"].checked,false);
  elems["metadata-goal"].value="check required files";
  elems["metadata-goal"].fire("change");
  assert.equal(elems["meta-approve"].disabled,true);
  elems.required.value="README.md\nnot-here.pdf";
  await click("meta-preview"); assert.equal(elems.required.value,"","raw checklist cleared from DOM");
  assert.equal(elems["metadata-consent"].checked,false);
  assert.equal(elems["meta-approve"].disabled,true);
  await click("meta-cancel");
  assert.match(elems["metadata-summary"].textContent,/CANCELED/);
  // G176: a failed cancel reply must not retain a usable ticket or consent.
  elems.required.value="README.md\nnot-here.pdf";
  await click("meta-preview");
  elems["metadata-consent"].checked=true;
  elems["metadata-consent"].fire("change");
  rejectOneMetadataCancel = true;
  await click("meta-cancel");
  assert.equal(elems["metadata-consent"].checked,false,"cancel error revokes consent");
  assert.equal(elems.required.value,"","cancel error clears private input");
  assert.equal(elems["meta-approve"].disabled,true,"cancel error forbids old approval");
  assert.equal(elems["meta-cancel"].disabled,true,"cancel error forbids stale cancel");
  assert.match(elems["metadata-summary"].textContent,/검토 세션 없음/);
  assert.match(elems.notice.textContent,/요청 거부|연결 오류/);
  elems.required.value="README.md\nnot-here.pdf";
  await click("meta-preview");
  elems["metadata-consent"].checked=true; elems["metadata-consent"].fire("change");
  assert.equal(elems["meta-approve"].disabled,false,"first review is approvable");
  // A failed replacement preview must revoke BOTH the old review and consent.
  elems.required.value="../blocked.txt";
  await click("meta-preview");  // backend rejects traversal; act catches HTTP 400
  assert.equal(elems.required.value,"","rejected raw path scrubbed from DOM");
  assert.equal(elems["metadata-consent"].checked,false,"old metadata consent revoked");
  assert.equal(elems["meta-approve"].disabled,true,"old review cannot be approved");
  assert.match(elems["metadata-summary"].textContent,/검토 세션 없음/);
  assert.match(elems.notice.textContent,/요청 거부|연결 오류/);
  // A valid replacement after a refusal still needs a NEW explicit consent.
  elems.required.value="secret-private-name.txt";
  await click("meta-preview");
  assert.equal(elems.required.value,"","new raw path cleared");
  assert.equal(elems["metadata-consent"].checked,false);
  assert.equal(elems["meta-approve"].disabled,true,"new ticket needs fresh checkbox");
  // Refuse blank new input even if a good review was open.
  elems.required.value="";
  await click("meta-preview");
  assert.equal(elems["meta-approve"].disabled,true,"blank preview revokes old ticket");
  elems.required.value="README.md\nnot-here.pdf";
  await click("meta-preview");
  elems["metadata-consent"].checked=true; elems["metadata-consent"].fire("change");
  rejectOneMetadataApproval = true;  // ambiguous delivery: client gets HTTP 503
  await click("meta-approve");
  assert.equal(elems["metadata-consent"].checked,false,"failed approval revokes consent");
  assert.equal(elems["meta-approve"].disabled,true,"failed approval must not be retried using old ticket");
  assert.match(elems["metadata-summary"].textContent,/검토 세션 없음/);
  // New, separately reviewed scope and explicit approval still works.
  elems.required.value="README.md\nnot-here.pdf";
  await click("meta-preview");
  assert.equal(elems["meta-approve"].disabled,true,"replacement ticket needs fresh consent");
  elems["metadata-consent"].checked=true; elems["metadata-consent"].fire("change");
  await click("meta-approve");
  assert.match(elems["metadata-summary"].textContent,/LOCAL_METADATA_BLOCKED/);
  assert.doesNotMatch(elems.output.textContent,/not-here\.pdf|README\.md/);
  await click("meta-status");
  assert.equal(elems["meta-save"].disabled,true,"redacted SQLite requires a second consent");
  elems["meta-save-consent"].checked=true;
  elems["meta-save-consent"].fire("change");
  assert.equal(elems["meta-save"].disabled,false,"explicit receipt consent allows save");
  await click("meta-save");
  assert.equal(elems["meta-save-consent"].checked,false,"one-use save consent must be cleared");
  assert.equal(elems["meta-save"].disabled,true,"the consumed review cannot be resent");
  assert.match(elems.output.textContent,/REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS/);
  assert.doesNotMatch(elems.output.textContent,/not-here\.pdf|README\.md/);
  await click("meta-readback");
  assert.match(elems.output.textContent,/REDACTED_LOCAL_METADATA_EVIDENCE_STORED_NOT_NAS/);
  assert.match(elems.output.textContent,/"state": "MISSING"/);
  assert.equal(elems["meta-export"].disabled,true,"no report can be exported before readback");
  await click("meta-council");
  assert.match(elems.output.textContent,/LOCAL_BLOCKED_MISSING_FILES/);
  assert.match(elems.output.textContent,/Architect/);
  assert.match(elems.output.textContent,/QA/);
  await click("meta-report");
  assert.match(elems.output.textContent,/OWNER_LOCAL_REPORT_READY_NOT_NAS/);
  await click("native-handoff");
  assert.match(elems.output.textContent,/NATIVE_EXECUTION_BLOCKED_PENDING_RUNTIME_EVIDENCE/);
  assert.doesNotMatch(elems.output.textContent,/not-here\\.pdf|README\\.md/);
  assert.equal(JSON.parse(elems.output.textContent).nas_verified,false);
  assert.equal(elems["meta-export"].disabled,false);
  await click("meta-export");
  assert.equal(globalThis.__downloads,3,"synthetic CSV, version JSON and local report");
  assert.match(elems["local-council-state"].textContent,/NAS 미검증/);
  // G231 owner-selected candidate exists, exact item does not: review required.
  elems.required.value="README-v1.md";
  elems["version-candidates"].value="README-v1.md=README.md";
  await click("meta-preview");
  assert.equal(elems.required.value,"");
  assert.equal(elems["version-candidates"].value,"");
  assert.equal(elems["meta-export"].disabled,true,"new inspection revokes stale report export");
  assert.equal(JSON.parse(elems.output.textContent).version_candidate_count,1);
  elems["metadata-consent"].checked=true;elems["metadata-consent"].fire("change");
  await click("meta-approve");
  assert.match(elems.output.textContent,/VERSION_REVIEW/);
  assert.doesNotMatch(elems.output.textContent,/README-v1.md|README.md/);
  // G232: actual two-stage local pipeline, same one-use read/save consent.
  await click("create");
  elems["text-workflow"].value =
    "파일 확인: README.md; 버전 비교: delivery.pdf => README-other.md";
  await click("text-preview");
  assert.equal(elems["text-workflow"].value,"","raw private instructions scrubbed");
  assert.equal(elems["metadata-consent"].checked,false);
  assert.match(elems.output.textContent,/"parsed_actions_count": 2/);
  assert.match(elems.output.textContent,/HANDOFF_CHECKLIST|REVIEW_VERSIONS/);
  assert.doesNotMatch(elems.output.textContent,/README.md|delivery.pdf|README-other.md/);
  elems["metadata-consent"].checked=true;elems["metadata-consent"].fire("change");
  await click("meta-approve");
  assert.match(elems.output.textContent,/LOCAL_METADATA_BLOCKED/);
  elems["meta-save-consent"].checked=true;elems["meta-save-consent"].fire("change");
  await click("meta-save");
  assert.match(elems.output.textContent,/"stage_layout"/);
  await click("meta-council");
  assert.match(elems.output.textContent,/"stage_reviews"/);
  await click("meta-report");
  assert.match(elems.output.textContent,/Stage 1/);
  assert.match(elems.output.textContent,/Stage 2/);
  assert.doesNotMatch(elems.output.textContent,/README.md|delivery.pdf|README-other.md/);
  elems.required.value="private-raw-path.txt";
  elems["advice-disk"].value="97";
  elems["advice-consent"].checked=true;
  elems.existing.value=workflowId;
  elems.token.value="short";
  await click("connect");  // refusal must discard the PREVIOUS valid bearer
  assert.equal(elems.required.value,"","reauth must scrub private textarea");
  assert.equal(elems["version-candidates"].value,"","reauth must scrub version paths");
  assert.equal(elems["advice-disk"].value,"","reauth scrubs manual samples");
  assert.equal(elems["advice-consent"].checked,false,"reauth revokes advice consent");
  assert.equal(elems.existing.value,"","reauth must clear previous workflow selection");
  assert.equal(elems.create.disabled,true,"bad reauth cannot retain previous token");
  assert.equal(elems.token.value,"");
  elems.token.value=auth;
  await click("connect");  // fresh auth required after bad attempt
  assert.equal(elems.create.disabled,false);
  // Use a disposable local CSV fixture; never owner/NAS data.
  const owned = fs.mkdtempSync(path.join(os.tmpdir(), "flowpilot-g239-node-"));
  try {
    const csvFile = path.join(owned, "test-owned.csv");
    fs.writeFileSync(csvFile,
      "customer,amount_cents\nalice,125\nbob,300\nalice,275\n");
    // G242 intent is parsed without file access; unsafe/compound requests
    // fail closed and revoke old approvals.
    const beforeIntentGet=csvGetCount, beforeIntentPost=csvRunPostCount;
    elems["csv-intent"].value="고객별 매출 합계와 NAS 삭제";
    await click("csv-intent-apply");
    assert.equal(elems["csv-intent"].value,"");
    assert.match(elems.notice.textContent,/요청 거부/);
    assert.equal(elems["csv-run"].disabled,true);
    elems["csv-intent"].value="부서별 매출 합계";
    await click("csv-intent-apply");
    assert.equal(elems["csv-group-column"].value,"department");
    assert.match(elems.output.textContent,/TYPED_LOCAL_INTENT_ONLY_NO_READ/);
    assert.equal(JSON.parse(elems.output.textContent).source_file_touched,false);
    assert.equal(elems["csv-consent"].checked,false);
    elems["csv-intent"].value="sum revenue by project";
    await click("csv-intent-apply");
    assert.equal(elems["csv-group-column"].value,"project");
    elems["csv-intent"].value="고객별 매출 합계";
    await click("csv-intent-apply");
    assert.equal(elems["csv-group-column"].value,"customer");
    assert.equal(csvGetCount,beforeIntentGet,"intent must not make a GET");
    assert.equal(csvRunPostCount,beforeIntentPost,"intent must not execute");
    elems["csv-local-path"].value = csvFile;
    elems["csv-group-column"].value = "customer";
    assert.equal(elems["csv-run"].disabled,true,"read must require separate consent");
    await click("csv-preview");
    assert.equal(elems["csv-local-path"].value,"","path cleared before run");
    assert.match(elems.output.textContent,/WAITING_EXPLICIT_LOCAL_CSV_JOB_APPROVAL/);
    assert.equal(elems["csv-run"].disabled,true,"preview is not execution consent");
    assert.equal(elems["csv-export"].disabled,true,"cannot export a preview");
    elems["csv-export-consent"].checked=true;elems["csv-export-consent"].fire("change");
    assert.equal(elems["csv-export"].disabled,true,"no receipt before run");
    elems["csv-consent"].checked=true;elems["csv-consent"].fire("change");
    rejectOneCsvRunReply=true;
    await click("csv-run");
    assert.equal(csvRunPostCount,1,"one committed POST even with lost reply");
    assert.match(elems.notice.textContent,/요청 거부|연결 오류/);
    assert.equal(elems["csv-consent"].checked,false);
    assert.equal(elems["csv-run"].disabled,true,"lost reply cannot rerun");
    assert.equal(elems["csv-export"].disabled,true,"lost reply cannot export");
    await click("csv-readback");
    assert.equal(csvRunPostCount,1,"GET must not rerun CSV");
    assert.equal(csvGetCount,1);
    assert.match(elems.output.textContent,/COMPLETE_LOCAL_TYPED_CSV_NOT_NAS/);
    assert.doesNotMatch(elems.output.textContent,/alice|bob|test-owned\.csv/);
    assert.equal(elems["csv-export"].disabled,true,"fresh consent after readback");
    elems["csv-export-consent"].checked=true;elems["csv-export-consent"].fire("change");
    assert.equal(elems["csv-export"].disabled,false);
    let exportedBlob;
    const savedCreate=URL.createObjectURL;
    URL.createObjectURL=function(blob){exportedBlob=blob;return savedCreate.call(URL,blob);};
    try{await click("csv-export");}finally{URL.createObjectURL=savedCreate;}
    assert.equal(globalThis.__downloads,4,"synthetic CSV + version JSON + metadata + G240 JSON");
    assert.equal(elems["csv-export-consent"].checked,false);
    assert.equal(elems["csv-export"].disabled,true);
    const result=JSON.parse(await exportedBlob.text());
    assert.equal(result.schema,"flowpilot-g240-redacted-csv-export-v1");
    assert.equal(result.group_count,2);
    assert.deepEqual(result.redacted_group_totals.map(x=>x.total_cents),[400,300]);
    assert.equal(result.owner_path_included,false);
    assert.equal(result.group_labels_included,false);
    assert.equal(result.nas_verified,false);
    assert.doesNotMatch(JSON.stringify(result),/alice|bob|test-owned\.csv/);
    assert.equal(fs.readFileSync(csvFile,"utf8").includes("alice,125"),true,
                 "owner-like synthetic source never changed");
    const recorded=elems["csv-job-status"].textContent.match(/csv_[0-9a-f]{24}/)?.[0];
    assert(recorded,"operator must have a visible job ID");
    await click("disconnect");
    elems.token.value=auth;
    await click("connect");
    assert.equal(elems["csv-readback"].disabled,true,"no automatic job persistence");
    const reads=csvGetCount;
    elems["csv-recover-id"].value="../invalid";
    await click("csv-recover");
    assert.equal(elems["csv-recover-id"].value,"");
    assert.equal(csvGetCount,reads,"invalid ID cannot hit HTTP");
    assert.equal(elems["csv-export"].disabled,true);
    elems["csv-recover-id"].value=recorded;
    await click("csv-recover");
    assert.equal(csvGetCount,reads+1,"manual recovery performs one GET");
    assert.equal(csvRunPostCount,1,"no second CSV run POST");
    assert.match(elems.output.textContent,/COMPLETE_LOCAL_TYPED_CSV_NOT_NAS/);
    assert.equal(elems["csv-export"].disabled,true,"fresh opt-in required");
    elems["csv-export-consent"].checked=true;elems["csv-export-consent"].fire("change");
    assert.equal(elems["csv-export"].disabled,false);
    await click("csv-readback");
    assert.equal(elems["csv-export-consent"].checked,false,"GET revokes prior export consent");
    assert.equal(elems["csv-export"].disabled,true);
    assert.doesNotMatch(elems.output.textContent,/alice|bob|test-owned\.csv/);
    // G243 history must require new consent; no client-side auto retrieval.
    assert.equal(elems["csv-history-list"].disabled,true);
    assert.equal(csvHistoryGetCount,0);
    elems["csv-history-consent"].checked=true;
    elems["csv-history-consent"].fire("change");
    await click("csv-history-list");
    assert.equal(csvHistoryGetCount,1,"history read only on user review");
    assert.equal(elems["csv-history-consent"].checked,false);
    assert.equal(elems["csv-history-list"].disabled,true);
    assert.equal(elems["csv-history-select"].options.length,2,"placeholder plus one");
    const listed=JSON.parse(elems.output.textContent);
    assert.equal(listed.schema,"flowpilot-g243-csv-history-v1");
    assert.equal(listed.jobs.length,1);
    assert.equal(listed.jobs[0].request_id,recorded);
    assert.doesNotMatch(JSON.stringify(listed),/alice|bob|test-owned\.csv/);
    elems["csv-history-select"].value=recorded;
    elems["csv-history-select"].fire("change");
    await click("csv-history-open");
    assert.equal(csvRunPostCount,1,"history reopening must not run");
    assert.equal(csvGetCount,reads+3,"history selection uses GET only");
    assert.equal(elems["csv-export"].disabled,true,"history is not export consent");

    // G244 separate owner-consented full CSV report, not the redacted JSON.
    const reportPath=path.join(owned,"new-full-report.csv");
    elems["csv-local-path"].value=csvFile;
    elems["csv-report-path"].value=reportPath;
    await click("csv-preview");
    assert.equal(elems["csv-report-consent"].checked,false,
                 "new preview revokes past write consent");
    const boundPreview=JSON.parse(elems.output.textContent);
    assert.equal(boundPreview.create_only_report_planned,true);
    assert.match(boundPreview.report_destination_sha256,/^[0-9a-f]{64}$/);
    assert.equal(boundPreview.report_path_in_response,false);
    assert.doesNotMatch(JSON.stringify(boundPreview),/new-full-report\.csv/);
    elems["csv-report-path"].value=path.join(owned,"unreviewed-target.csv");
    elems["csv-report-path"].fire("input");
    elems["csv-consent"].checked=true;elems["csv-consent"].fire("change");
    elems["csv-report-consent"].checked=true;elems["csv-report-consent"].fire("change");
    assert.equal(elems["csv-run"].disabled,true,
                 "changed output scope cannot inherit old approval");
    elems["csv-report-path"].value=reportPath;elems["csv-report-path"].fire("input");
    assert.equal(elems["csv-run"].disabled,false,
                 "exact reviewed destination plus both consents enables run");
    elems["csv-consent"].checked=false;elems["csv-consent"].fire("change");
    elems["csv-report-consent"].checked=false;elems["csv-report-consent"].fire("change");
    elems["csv-consent"].checked=true;
    elems["csv-consent"].fire("change");
    assert.equal(elems["csv-run"].disabled,true,
                 "write destination without separate approval blocks run");
    elems["csv-report-consent"].checked=true;
    elems["csv-report-consent"].fire("change");
    assert.equal(elems["csv-run"].disabled,false);
    await click("csv-run");
    assert.equal(csvRunPostCount,2);
    assert.equal(elems["csv-report-path"].value,"","private path cleared");
    assert.equal(elems["csv-report-consent"].checked,false);
    assert.equal(fs.readFileSync(reportPath,"utf8"),
      "customer,total_cents,source_rows\nalice,400,2\nbob,300,1\n");
    const fullReceipt=JSON.parse(elems.output.textContent);
    assert.equal(fullReceipt.result.report_file_created,true);
    assert.doesNotMatch(JSON.stringify(fullReceipt),/new-full-report\.csv|alice|bob/);
    assert.equal(fs.readFileSync(csvFile,"utf8").includes("alice,125"),true);
    assert.equal(elems["csv-run"].disabled,true,"one shot not repeated");
    await click("csv-readback");
    assert.match(elems.output.textContent,/COMPLETE_LOCAL_TYPED_CSV_NOT_NAS/);
    assert.equal(elems["csv-export"].disabled,true,"fresh export consent after GET");
    // G245 verify a real previously created report; separate consent only.
    assert.equal(elems["csv-verify-report"].disabled,true);
    elems["csv-verify-path"].value=reportPath;elems["csv-verify-path"].fire("input");
    assert.equal(elems["csv-verify-report"].disabled,true);
    elems["csv-verify-consent"].checked=true;elems["csv-verify-consent"].fire("change");
    assert.equal(elems["csv-verify-report"].disabled,false);
    await click("csv-verify-report");
    assert.equal(csvVerifyPostCount,1);
    assert.equal(elems["csv-verify-path"].value,"");
    assert.equal(elems["csv-verify-consent"].checked,false);
    assert.equal(JSON.parse(elems.output.textContent).status,
                 "VERIFIED_LOCAL_OUTPUT_SHA_NOT_NAS");
    fs.writeFileSync(reportPath,
      fs.readFileSync(reportPath,"utf8").replace("400","401"));
    elems["csv-verify-path"].value=reportPath;elems["csv-verify-path"].fire("input");
    elems["csv-verify-consent"].checked=true;elems["csv-verify-consent"].fire("change");
    await click("csv-verify-report");
    assert.equal(csvVerifyPostCount,2);
    assert.equal(JSON.parse(elems.output.textContent).status,
                 "CONFLICT_LOCAL_OUTPUT_SHA_NOT_NAS");
    assert.equal(csvRunPostCount,2,"verifier never reruns CSV job");
    assert.equal(fs.readFileSync(csvFile,"utf8").includes("alice,125"),true);
  } finally {fs.rmSync(owned,{recursive:true,force:true});}
  await click("disconnect");
  assert.equal(elems["csv-local-path"].value,"","disconnect clears file path");
  assert.equal(elems["csv-readback"].disabled,true,"disconnect clears job ID");
  assert.equal(elems["csv-export"].disabled,true,"disconnect revokes CSV export");
  assert.equal(elems["csv-export-consent"].checked,false);
  assert.equal(elems.create.disabled,true);
  assert.equal(elems.token.value,"");
  process.stdout.write("G166_NODE_DOM_HTTP_SMOKE_PASS\n");
}
main().catch(error=>{process.stderr.write(String(error.stack||error)+"\n");process.exitCode=1;});
