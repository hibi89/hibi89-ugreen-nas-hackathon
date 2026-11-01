"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
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
let rejectOneMetadataApproval = false;
let rejectOneMetadataCancel = false;
globalThis.fetch = (route, init) => {
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
  return nativeFetch(base + route, init);
};
const ids = ["token","connect","disconnect","clear","connection-status","notice","output",
  "workflow-id","workflow-state","plan-hash","metadata-summary","goal","existing","create",
  "list","load","plan","guide","test","approve","run","audit","evidence","report","recover",
  "synthetic-consent","metadata-consent","required","meta-preview","meta-approve",
  "meta-cancel","meta-status"];
const buttonIds = ["connect","disconnect","clear","create","list","load","plan","guide",
  "test","approve","run","audit","evidence","report","recover","meta-preview",
  "meta-approve","meta-cancel","meta-status"];
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
  elems.token.value=auth;
  await click("connect");
  assert.equal(elems.token.value,"","token must clear from password DOM");
  assert.match(elems["connection-status"].textContent,/연결 확인/);
  await click("create");
  assert.match(elems["workflow-id"].textContent,/^wf_[0-9a-f]{32}$/);
  const workflowId=elems["workflow-id"].textContent;
  assert.equal(elems.guide.disabled,false,"guide requires a workflow");
  await click("guide");
  assert.match(elems.output.textContent,/합성 전용 7단계 운영 가이드/);
  assert.match(elems.output.textContent,/7\. 운영 전 승인 게이트/);
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
  await click("run");
  assert.equal(elems["workflow-state"].textContent,"COMPLETE_LOCAL_SYNTHETIC");
  await click("audit");assert.match(elems.output.textContent,/LOCAL_CHAIN_INTACT/);
  await click("evidence");assert.match(elems.output.textContent,/NOT_NAS/);
  await click("report");
  assert.equal(globalThis.__downloads,1,"one authenticated CSV download after digest verified");
  assert.match(elems.output.textContent,/LOCAL_SYNTHETIC_CSV_SHA_VERIFIED/);
  await click("list");
  assert(elems.existing.options.some(x=>x.value===workflowId),"workflow listed from SQLite");
  elems.existing.value=workflowId;elems.existing.fire("change");
  await click("load");assert.equal(elems["workflow-state"].textContent,"COMPLETE_LOCAL_SYNTHETIC");
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
  elems.required.value="private-raw-path.txt";
  elems.existing.value=workflowId;
  elems.token.value="short";
  await click("connect");  // refusal must discard the PREVIOUS valid bearer
  assert.equal(elems.required.value,"","reauth must scrub private textarea");
  assert.equal(elems.existing.value,"","reauth must clear previous workflow selection");
  assert.equal(elems.create.disabled,true,"bad reauth cannot retain previous token");
  assert.equal(elems.token.value,"");
  elems.token.value=auth;
  await click("connect");  // fresh auth required after bad attempt
  assert.equal(elems.create.disabled,false);
  await click("disconnect");
  assert.equal(elems.create.disabled,true);
  assert.equal(elems.token.value,"");
  process.stdout.write("G166_NODE_DOM_HTTP_SMOKE_PASS\n");
}
main().catch(error=>{process.stderr.write(String(error.stack||error)+"\n");process.exitCode=1;});
