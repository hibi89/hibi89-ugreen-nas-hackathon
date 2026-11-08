"""Optional real Chromium dashboard E2E against disposable local HTTP/SQLite.

Requires installed Playwright and a compatible local browser binary.
Never installs dependencies, calls UGREEN, starts a trial or opens owner files.
A pass is real browser *local synthetic* verification only.
"""
from __future__ import annotations
from contextlib import suppress
from hashlib import sha256
import json
from pathlib import Path
import re
import secrets
import shutil
from tempfile import TemporaryDirectory
import threading
from traceback import extract_tb

from flowpilot_local_backend import Backend, create_server


def run_browser():
    try:
        from playwright.sync_api import sync_playwright, expect
    except ImportError:
        return {"status":"REAL_BROWSER_NOT_VERIFIED", "reason":"PLAYWRIGHT_NOT_INSTALLED",
                "release_gate":"HOLD"}
    with TemporaryDirectory(prefix="g167-browser-") as temp:
        folder=Path(temp)
        root=folder/"disposable-local-root"
        root.mkdir()
        (root/"README.md").write_bytes(b"G167 safe disposable example\n")
        token=secrets.token_urlsafe(48)
        server=create_server(Backend(folder/"new.sqlite",create=True,metadata_root=root),
                             token,port=0)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        errors=[]
        browser=None
        try:
            with sync_playwright() as playwright:
                # Prefer the host's already-installed Chrome. Attempting
                # Playwright's absent bundled Chromium wastes a full timeout
                # and makes headless CI vulnerable to transient runner load.
                binary=next((shutil.which(name) for name in
                             ("chromium","chromium-browser","google-chrome","msedge")
                             if shutil.which(name)),None)
                try:
                    browser=playwright.chromium.launch(
                        executable_path=binary,headless=True,timeout=60000)
                except Exception:
                    # Browser execution can be environment-blocked. Never
                    # substitute a mocked DOM and never report a false PASS.
                    raise
                context=browser.new_context(accept_downloads=True)
                page=context.new_page()
                page.on("pageerror",lambda error: errors.append(str(error)))
                page.on("console",lambda message: errors.append(message.text)
                        if message.type=="error" else None)
                page.on("requestfailed",lambda request: errors.append(
                    "network:"+request.url.split("?")[0]))
                address=f"http://127.0.0.1:{server.server_port}/dashboard"
                page.goto(address,wait_until="load",timeout=12000)
                assert page.locator("h1").inner_text()=="FlowPilot 3.0"
                assert page.locator("#create").is_disabled()
                page.locator("#token").fill(token)
                page.locator("#connect").click()
                expect(page.locator("#connection-status")).to_contain_text("로컬 연결 확인")
                assert page.locator("#token").input_value()==""
                # G180: explicit, manually entered synthetic metrics only.
                expect(page.locator("#advice-submit")).to_be_disabled()
                page.locator("#advice-disk").fill("95")
                expect(page.locator("#advice-submit")).to_be_disabled()
                page.locator("#advice-errors").fill("3")
                page.locator("#advice-backup").fill("73")
                page.locator("#advice-consent").check()
                page.locator("#advice-submit").click()
                expect(page.locator("#output")).to_contain_text("제안 건수: 3")
                expect(page.locator("#output")).to_contain_text("디스크 용량 검토")
                expect(page.locator("#output")).to_contain_text("반복 오류 로그 검토")
                expect(page.locator("#output")).to_contain_text("백업 주기 검토")
                expect(page.locator("#output")).to_contain_text("실제 NAS 수집/검증 없음")
                assert page.locator("#advice-disk").input_value()==""
                assert page.locator("#advice-errors").input_value()==""
                assert page.locator("#advice-backup").input_value()==""
                expect(page.locator("#advice-consent")).not_to_be_checked()
                expect(page.locator("#advice-submit")).to_be_disabled()
                page.locator("#advice-disk").fill("20")
                page.locator("#advice-consent").check()
                page.locator("#advice-submit").click()
                expect(page.locator("#output")).to_contain_text("NO_ALERTS_IN_SUPPLIED_DATA")
                expect(page.locator("#output")).to_contain_text("미입력 항목: 2개")
                page.locator("#advice-disk").fill("101")
                page.locator("#advice-consent").check()
                page.locator("#advice-submit").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부")
                expect(page.locator("#advice-consent")).not_to_be_checked()
                expect(page.locator("#advice-submit")).to_be_disabled()
                page.locator("#create").click()
                expect(page.locator("#workflow-state")).to_have_text("PLANNED")
                page.locator("#guide").click()
                expect(page.locator("#output")).to_contain_text("합성 전용 7단계 운영 가이드")
                expect(page.locator("#output")).to_contain_text("현재 실행 상태: PLANNED")
                expect(page.locator("#output")).to_contain_text("로컬 검증 단계: 2/6")
                expect(page.locator("#output")).to_contain_text("3. [NEXT] 4역할 합성 검증")
                expect(page.locator("#output")).to_contain_text("브라우저 대조 완료")
                expect(page.locator("#output")).to_contain_text("7. [OFFICIAL_BLOCKED]")
                expect(page.locator("#output")).to_contain_text("NAS / Uliya / Docker 실행 검증 아님")
                page.locator("#plan").click()
                expect(page.locator("#plan-hash")).to_contain_text("검증한 계획 SHA-256")
                assert page.locator("#approve").is_disabled()
                page.locator("#test").click()
                expect(page.locator("#workflow-state")).to_have_text("TESTED")
                page.locator("#plan").click()
                page.locator("#synthetic-consent").check()
                # G283: the real backend commits consent, but HTTP response
                # becomes invalid. Never keep approval enabled or retry POST.
                tested_id=page.locator("#workflow-id").inner_text()
                approval_replies=[]
                def obscure_approved_reply(route):
                    upstream=route.fetch()
                    approval_replies.append(
                        (upstream.status, upstream.json().get("status")))
                    route.fulfill(status=200, content_type="application/json",
                                  body="{")
                page.route("**/v1/workflows/" + tested_id + "/approve",
                           obscure_approved_reply, times=1)
                page.locator("#approve").click()
                assert approval_replies == [(200, "APPROVED_SYNTHETIC")]
                expect(page.locator("#notice")).to_contain_text(
                    "요청 거부 또는 연결 오류")
                expect(page.locator("#workflow-state")).to_contain_text(
                    "결과 미확인")
                expect(page.locator("#approve")).to_be_disabled()
                expect(page.locator("#run")).to_be_disabled()
                expect(page.locator("#refresh")).to_be_enabled()
                expect(page.locator("#synthetic-consent")).not_to_be_checked()
                # Explicit GET-only reconciliation recovers the committed
                # state without issuing a second approval operation.
                page.locator("#refresh").click()
                expect(page.locator("#workflow-state")).to_have_text(
                    "APPROVED_SYNTHETIC")
                expect(page.locator("#run")).to_be_enabled()
                assert approval_replies == [(200, "APPROVED_SYNTHETIC")]

                # G282: an uncertain new Create reply must not retain a
                # previously approved executable workflow in the browser.
                approved_id=page.locator("#workflow-id").inner_text()
                expect(page.locator("#run")).to_be_enabled()
                page.route("**/v1/workflows",
                           lambda route: route.fulfill(
                               status=200, content_type="application/json", body="{"),
                           times=1)
                page.locator("#create").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#workflow-state")).to_have_text("미생성")
                expect(page.locator("#run")).to_be_disabled()
                expect(page.locator("#synthetic-consent")).not_to_be_checked()

                # A failed Load must also keep old approval revoked, and a
                # fresh GET to the SAME existing ID may safely reestablish it.
                page.locator("#list").click()
                page.locator("#existing").select_option(approved_id)
                page.route("**/v1/workflows/" + approved_id,
                           lambda route: route.fulfill(
                               status=200, content_type="application/json", body="{"),
                           times=1)
                page.locator("#load").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#workflow-state")).to_have_text("미생성")
                expect(page.locator("#run")).to_be_disabled()
                page.locator("#load").click()
                expect(page.locator("#workflow-state")).to_have_text("APPROVED_SYNTHETIC")
                expect(page.locator("#run")).to_be_enabled()
                page.locator("#run").click()
                expect(page.locator("#workflow-state")).to_have_text("COMPLETE_LOCAL_SYNTHETIC")
                page.locator("#guide").click()
                expect(page.locator("#output")).to_contain_text("현재 실행 상태: COMPLETE_LOCAL_SYNTHETIC")
                expect(page.locator("#output")).to_contain_text("로컬 검증 단계: 6/6")
                expect(page.locator("#output")).to_contain_text("6. [VERIFIED_LOCAL] 감사·산출물")
                expect(page.locator("#output")).to_contain_text("7. [OFFICIAL_BLOCKED]")
                page.locator("#audit").click()
                expect(page.locator("#output")).to_contain_text("LOCAL_CHAIN_INTACT")
                page.locator("#evidence").click()
                expect(page.locator("#output")).to_contain_text("LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS")
                with page.expect_download(timeout=8000) as transfer:
                    page.locator("#report").click()
                download=transfer.value
                saved=folder/"browser-fixture.csv"
                download.save_as(saved)
                assert saved.stat().st_size>0
                assert sha256(saved.read_bytes()).hexdigest() in page.locator("#output").inner_text()
                page.locator("#required").fill("README.md\nmissing.pdf")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                assert page.locator("#required").input_value()==""
                assert page.locator("#meta-approve").is_disabled()
                page.locator("#metadata-consent").check()
                page.locator("#meta-approve").click()
                expect(page.locator("#metadata-summary")).to_contain_text("LOCAL_METADATA_BLOCKED")

                # G248: use REAL Chromium against the local-only MetadataGate,
                # with an actual disposable competing version file pair.
                release=root/"release"
                release.mkdir()
                source_v1=release/"final.pdf"
                source_v2=release/"final_v2.pdf"
                source_v1.write_bytes(b"g248 version one synthetic")
                source_v2.write_bytes(b"g248 version two synthetic")
                page.locator("#metadata-goal").select_option("버전 비교해줘")
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#required").fill("release/final.pdf")
                page.locator("#meta-preview").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부")
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#required").fill("release/final.pdf")
                page.locator("#version-candidates").fill(
                    "release/final.pdf=release/final_v2.pdf")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text(
                    "WAITING_APPROVAL")
                g248_preview=json.loads(page.locator("#output").inner_text())
                assert g248_preview["selected_intent"]=="REVIEW_VERSIONS"
                assert len(g248_preview["typed_review_plan"])==4
                assert g248_preview["inspection_result"] is None
                assert str(root) not in page.locator("#output").inner_text()
                assert "final_v2.pdf" not in page.locator("#output").inner_text()
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#metadata-consent").check()
                page.locator("#meta-approve").click()
                expect(page.locator("#metadata-summary")).to_contain_text(
                    "LOCAL_METADATA_BLOCKED")
                g248_result=json.loads(page.locator("#output").inner_text())
                assert g248_result["selected_intent"]=="REVIEW_VERSIONS"
                assert g248_result["inspection_result"]==[
                    {"index":1,"state":"VERSION_REVIEW"}]
                assert g248_result["nas_verified"] is False
                assert g248_result["file_contents_opened"] is False
                assert source_v1.read_bytes()==b"g248 version one synthetic"
                assert source_v2.read_bytes()==b"g248 version two synthetic"
                # G250 authentic Chromium download of only the closed-schema review.
                expect(page.locator("#version-export")).to_be_disabled()
                page.locator("#version-export-consent").check()
                with page.expect_download(timeout=8000) as transfer:
                    page.locator("#version-export").click()
                version_output=folder/"g250-version-evidence.json"
                transfer.value.save_as(version_output)
                raw=version_output.read_text(encoding="utf-8")
                result=json.loads(raw)
                assert result["schema"]=="flowpilot-local-version-evidence-g249-v1"
                assert result["findings"]==[{"index":1,"state":"VERSION_REVIEW"}]
                assert result["manual_owner_review_required"] is True
                assert result["auto_selected_final_version"] is False
                assert result["nas_verified"] is False
                assert result["release_gate"]=="HOLD"
                assert str(root) not in raw
                assert "final_v2.pdf" not in raw
                assert "release/final.pdf" not in raw
                assert source_v1.read_bytes()==b"g248 version one synthetic"
                assert source_v2.read_bytes()==b"g248 version two synthetic"
                expect(page.locator("#version-export-consent")).not_to_be_checked()
                expect(page.locator("#version-export")).to_be_disabled()
                expect(page.locator("#meta-approve")).to_be_disabled()
                # G254: real Chromium exact text -> scope -> explicitly
                # consented read -> redacted download, no NAS or file changes.
                page.locator("#version-intent").fill(
                    "버전 비교: release/final.pdf => ../outside.pdf")
                page.locator("#version-intent-apply").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부")
                expect(page.locator("#meta-approve")).to_be_disabled()
                assert page.locator("#version-intent").input_value()==""
                page.locator("#version-intent").fill(
                    "compare versions: release/final.pdf => release/final_v2.pdf")
                page.locator("#version-intent-apply").click()
                assert page.locator("#metadata-goal").input_value()=="review versions"
                assert page.locator("#required").input_value()=="release/final.pdf"
                assert page.locator("#version-candidates").input_value()==(
                    "release/final.pdf=release/final_v2.pdf")
                parsed=json.loads(page.locator("#output").inner_text())
                assert parsed["status"]=="LOCAL_TYPED_VERSION_SCOPE_NO_READ"
                assert parsed["local_metadata_read"] is False
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text(
                    "WAITING_APPROVAL")
                assert page.locator("#required").input_value()==""
                assert page.locator("#version-candidates").input_value()==""
                page.locator("#metadata-consent").check()
                page.locator("#meta-approve").click()
                expect(page.locator("#metadata-summary")).to_contain_text(
                    "LOCAL_METADATA_BLOCKED")
                expect(page.locator("#version-export")).to_be_disabled()
                page.locator("#version-export-consent").check()
                with page.expect_download(timeout=8000) as transfer:
                    page.locator("#version-export").click()
                evidence_path=folder/"g254-redacted.json"
                transfer.value.save_as(evidence_path)
                redacted=evidence_path.read_text(encoding="utf-8")
                result_g254=json.loads(redacted)
                assert result_g254["findings"]==[
                    {"index":1,"state":"VERSION_REVIEW"}]
                assert result_g254["nas_verified"] is False
                assert result_g254["auto_selected_final_version"] is False
                assert "release/final.pdf" not in redacted
                assert "release/final_v2.pdf" not in redacted
                assert source_v1.read_bytes()==b"g248 version one synthetic"
                assert source_v2.read_bytes()==b"g248 version two synthetic"
                expect(page.locator("#version-export-consent")).not_to_be_checked()
                page.locator("#metadata-goal").select_option("check required files")
                expect(page.locator("#meta-approve")).to_be_disabled()
                # G175: the actual localhost server consumes a one-use metadata
                # approval, but the browser receives a corrupt reply. The
                # UI must revoke the consumed ticket and approval immediately.
                page.locator("#required").fill("README.md")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                page.locator("#metadata-consent").check()
                consumed=[]
                def obscure_consumed_approval(route):
                    upstream=route.fetch()
                    consumed.append((upstream.status,upstream.json().get("status")))
                    # A 200 with an interrupted JSON body mimics a lost reply
                    # without creating a noisy intentional HTTP error in Chrome.
                    route.fulfill(status=200,content_type="application/json",body="{")
                page.route("**/v1/local-metadata/approve", obscure_consumed_approval, times=1)
                page.locator("#meta-approve").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#metadata-summary")).to_have_text("검토 세션 없음")
                assert consumed==[(200,"LOCAL_METADATA_FINDINGS_READY")]
                assert page.locator("#required").input_value()==""
                expect(page.locator("#metadata-consent")).not_to_be_checked()
                expect(page.locator("#meta-approve")).to_be_disabled()

                # Only a fresh preview and new explicit consent may approve
                # a second read after an uncertain first response.
                page.locator("#required").fill("README.md")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#metadata-consent").check()
                page.locator("#meta-approve").click()
                expect(page.locator("#metadata-summary")).to_contain_text(
                    "LOCAL_METADATA_FINDINGS_READY")

                # Starting a new preview must invalidate an older actionable
                # ticket/checkbox even if the new preview response is broken.
                page.locator("#required").fill("README.md")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                page.locator("#metadata-consent").check()
                page.route("**/v1/local-metadata/preview",
                           lambda route: route.fulfill(
                               status=200, content_type="application/json", body="{"),
                           times=1)
                page.locator("#required").fill("../restricted-private-path")
                page.locator("#meta-preview").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#metadata-summary")).to_have_text("검토 세션 없음")
                assert page.locator("#required").input_value()==""
                expect(page.locator("#metadata-consent")).not_to_be_checked()
                expect(page.locator("#meta-approve")).to_be_disabled()

                # G176: real backend completes cancellation, but browser
                # loses the response. Old ticket and consent must be revoked.
                page.locator("#required").fill("README.md")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                page.locator("#metadata-consent").check()
                canceled = []
                def obscure_consumed_cancel(route):
                    upstream = route.fetch()
                    payload = upstream.json()
                    canceled.append((upstream.status, payload.get("status"),
                                     payload.get("approved_local_metadata_access")))
                    route.fulfill(status=200, content_type="application/json", body="{")
                page.route("**/v1/local-metadata/cancel", obscure_consumed_cancel, times=1)
                page.locator("#meta-cancel").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#metadata-summary")).to_have_text("검토 세션 없음")
                assert canceled == [(200, "CANCELED", False)]
                expect(page.locator("#metadata-consent")).not_to_be_checked()
                expect(page.locator("#meta-approve")).to_be_disabled()
                expect(page.locator("#meta-cancel")).to_be_disabled()
                assert page.locator("#required").input_value() == ""
                page.locator("#required").fill("README.md")
                page.locator("#meta-preview").click()
                expect(page.locator("#metadata-summary")).to_contain_text("WAITING_APPROVAL")
                expect(page.locator("#meta-approve")).to_be_disabled()
                page.locator("#meta-cancel").click()
                expect(page.locator("#metadata-summary")).to_contain_text("CANCELED")
                # G241: actual Chromium and localhost SQLite, no owner CSV or NAS.
                csv_fixture=folder/"g241-disposable.csv"
                csv_fixture.write_text("customer,amount_cents\nalice,125\nbob,300\nalice,275\n",
                                       encoding="utf-8")
                original=csv_fixture.read_bytes()
                post_requests=[]
                page.on("request",lambda req: post_requests.append(req.method)
                        if req.url.endswith("/v1/local-csv/run") else None)
                # G242: exact allowlisted Korean/English intents become a
                # local typed CSV plan; reject compound write/NAS commands.
                page.locator("#csv-intent").fill("고객별 매출 합계 + NAS 삭제")
                page.locator("#csv-intent-apply").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부")
                expect(page.locator("#csv-run")).to_be_disabled()
                assert page.locator("#csv-intent").input_value()==""
                page.locator("#csv-intent").fill("부서별 매출 합계")
                page.locator("#csv-intent-apply").click()
                expect(page.locator("#csv-group-column")).to_have_value("department")
                expect(page.locator("#output")).to_contain_text(
                    "TYPED_LOCAL_INTENT_ONLY_NO_READ")
                page.locator("#csv-intent").fill("sum revenue by project")
                page.locator("#csv-intent-apply").click()
                expect(page.locator("#csv-group-column")).to_have_value("project")
                page.locator("#csv-intent").fill("고객별 매출 합계")
                page.locator("#csv-intent-apply").click()
                expect(page.locator("#csv-group-column")).to_have_value("customer")
                expect(page.locator("#csv-run")).to_be_disabled()
                page.locator("#csv-local-path").fill(str(csv_fixture))
                expect(page.locator("#csv-run")).to_be_disabled()
                page.locator("#csv-preview").click()
                expect(page.locator("#output")).to_contain_text(
                    "WAITING_EXPLICIT_LOCAL_CSV_JOB_APPROVAL")
                assert page.locator("#csv-local-path").input_value()==""
                page.locator("#csv-consent").check()
                consumed_csv=[]
                def lose_csv_reply(route):
                    upstream=route.fetch()
                    consumed_csv.append((upstream.status,upstream.json().get("status")))
                    route.fulfill(status=200,content_type="application/json",body="{")
                page.route("**/v1/local-csv/run",lose_csv_reply,times=1)
                page.locator("#csv-run").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                expect(page.locator("#csv-run")).to_be_disabled()
                assert consumed_csv==[(200,"COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")]
                recorded=re.search(r"csv_[0-9a-f]{24}",
                                   page.locator("#csv-job-status").inner_text())
                assert recorded is not None
                job_id=recorded.group()
                page.locator("#csv-readback").click()
                expect(page.locator("#output")).to_contain_text("COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")
                expect(page.locator("#csv-export")).to_be_disabled()
                page.locator("#csv-export-consent").check()
                with page.expect_download(timeout=8000) as csv_download:
                    page.locator("#csv-export").click()
                saved_csv=folder/"g241-export.json"
                csv_download.value.save_as(saved_csv)
                result=json.loads(saved_csv.read_text(encoding="utf-8"))
                assert result["schema"]=="flowpilot-g240-redacted-csv-export-v1"
                assert result["request_id"]==job_id
                assert result["source_rows"]==3 and result["group_count"]==2
                assert [x["total_cents"] for x in result["redacted_group_totals"]]==[400,300]
                assert result["owner_path_included"] is False
                assert result["group_labels_included"] is False
                assert result["nas_verified"] is False
                assert not any(s in saved_csv.read_text(encoding="utf-8")
                               for s in ("alice","bob",str(csv_fixture)))
                assert csv_fixture.read_bytes()==original
                # A full reload must not persist the token or job ID.
                page.reload(wait_until="load")
                expect(page.locator("#csv-readback")).to_be_disabled()
                expect(page.locator("#csv-recover")).to_be_disabled()
                page.locator("#token").fill(token)
                page.locator("#connect").click()
                expect(page.locator("#connection-status")).to_contain_text("로컬 연결 확인")
                page.locator("#csv-recover-id").fill("../invalid")
                page.locator("#csv-recover").click()
                expect(page.locator("#notice")).to_contain_text("요청 거부 또는 연결 오류")
                assert page.locator("#csv-recover-id").input_value()==""
                page.locator("#csv-recover-id").fill(job_id)
                page.locator("#csv-recover").click()
                expect(page.locator("#output")).to_contain_text("COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")
                assert post_requests==["POST"],"recovery must not replay execution"
                expect(page.locator("#csv-export")).to_be_disabled()
                page.locator("#csv-export-consent").check()
                with page.expect_download(timeout=8000) as again:
                    page.locator("#csv-export").click()
                after=folder/"g241-recovered.json"
                again.value.save_as(after)
                assert json.loads(after.read_text(encoding="utf-8"))==result
                assert csv_fixture.read_bytes()==original
                # G243 requires a fresh one-use approval to see persistent IDs.
                expect(page.locator("#csv-history-list")).to_be_disabled()
                page.locator("#csv-history-consent").check()
                page.locator("#csv-history-list").click()
                expect(page.locator("#output")).to_contain_text(
                    "LOCAL_CSV_HISTORY_NOT_NAS")
                expect(page.locator("#csv-history-consent")).not_to_be_checked()
                expect(page.locator("#csv-history-list")).to_be_disabled()
                assert page.locator("#csv-history-select option").count()==2
                result_index=json.loads(page.locator("#output").inner_text())
                assert result_index["jobs"]==[{
                    "request_id":job_id,
                    "status":"COMPLETE_LOCAL_TYPED_CSV_NOT_NAS",
                    "group_count":2,
                    "source_rows":3
                }]
                assert not any(x in page.locator("#output").inner_text()
                               for x in ("alice","bob",str(csv_fixture)))
                page.locator("#csv-history-select").select_option(job_id)
                page.locator("#csv-history-open").click()
                expect(page.locator("#output")).to_contain_text(
                    "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")
                assert post_requests==["POST"]
                expect(page.locator("#csv-export")).to_be_disabled()
                # G244: owner approves a distinct create-only local full CSV.
                # This output contains synthetic labels and stays on the CI
                # runner; it is not a browser download or a NAS operation.
                report_target=folder/"g244-full-aggregate.csv"
                page.locator("#csv-local-path").fill(str(csv_fixture))
                page.locator("#csv-report-path").fill(str(report_target))
                page.locator("#csv-preview").click()
                expect(page.locator("#output")).to_contain_text("report_destination_sha256")
                expect(page.locator("#csv-report-consent")).not_to_be_checked()
                # G246: previewed destination is SHA-bound to the actual
                # one-time run; a changed path disables consent reuse.
                preview_scope=json.loads(page.locator("#output").inner_text())
                assert preview_scope["create_only_report_planned"] is True
                assert re.fullmatch(r"[0-9a-f]{64}",
                                    preview_scope["report_destination_sha256"])
                assert preview_scope["report_path_in_response"] is False
                assert str(report_target) not in page.locator("#output").inner_text()
                page.locator("#csv-report-path").fill(str(folder/"unreviewed.csv"))
                page.locator("#csv-consent").check()
                page.locator("#csv-report-consent").check()
                expect(page.locator("#csv-run")).to_be_disabled()
                page.locator("#csv-report-path").fill(str(report_target))
                expect(page.locator("#csv-run")).to_be_enabled()
                page.locator("#csv-run").click()
                expect(page.locator("#output")).to_contain_text(
                    "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")
                assert page.locator("#csv-report-path").input_value()==""
                expect(page.locator("#csv-report-consent")).not_to_be_checked()
                assert report_target.read_text(encoding="utf-8")==(
                    "customer,total_cents,source_rows\n"
                    "alice,400,2\nbob,300,1\n")
                report_receipt=json.loads(page.locator("#output").inner_text())
                assert report_receipt["result"]["report_file_created"] is True
                assert report_receipt["result"]["nas_verified"] is False
                assert str(report_target) not in page.locator("#output").inner_text()
                assert csv_fixture.read_bytes()==original
                expect(page.locator("#csv-run")).to_be_disabled()
                page.locator("#csv-readback").click()
                expect(page.locator("#output")).to_contain_text(
                    "COMPLETE_LOCAL_TYPED_CSV_NOT_NAS")
                expect(page.locator("#csv-export")).to_be_disabled()
                # G245 real GUI verifies recorded output SHA after G244;
                # a deliberate change must return CONFLICT without CSV rerun.
                expect(page.locator("#csv-verify-report")).to_be_disabled()
                page.locator("#csv-verify-path").fill(str(report_target))
                expect(page.locator("#csv-verify-report")).to_be_disabled()
                page.locator("#csv-verify-consent").check()
                page.locator("#csv-verify-report").click()
                expect(page.locator("#output")).to_contain_text(
                    "VERIFIED_LOCAL_OUTPUT_SHA_NOT_NAS")
                assert page.locator("#csv-verify-path").input_value()==""
                expect(page.locator("#csv-verify-consent")).not_to_be_checked()
                assert csv_fixture.read_bytes()==original
                report_target.write_bytes(report_target.read_bytes().replace(b"400",b"401"))
                page.locator("#csv-verify-path").fill(str(report_target))
                page.locator("#csv-verify-consent").check()
                page.locator("#csv-verify-report").click()
                expect(page.locator("#output")).to_contain_text(
                    "CONFLICT_LOCAL_OUTPUT_SHA_NOT_NAS")
                assert post_requests==["POST","POST"]
                assert csv_fixture.read_bytes()==original
                page.locator("#token").fill("short")
                page.locator("#connect").click()
                expect(page.locator("#create")).to_be_disabled()
                assert page.locator("#token").input_value()==""
                if errors:
                    raise RuntimeError("BROWSER_CONSOLE_OR_NETWORK_ERROR")
                context.close()
                return {
                    "status":"REAL_LOCAL_BROWSER_E2E_PASS_NOT_NAS",
                    "checks":["DOM_RENDER","TOKEN_CLEAR","PLAN_TEST_APPROVE_RUN",
                              "AUDIT_EVIDENCE","CSV_SHA_DOWNLOAD","METADATA_CONSENT",
                              "INVALID_REAUTH_CLEARS_AUTH",
                              "METADATA_APPROVAL_REPLY_LOSS_FAIL_CLOSED",
                              "METADATA_PREVIEW_FAILURE_REVOKES_CONSENT",
                              "METADATA_CANCEL_REPLY_LOSS_FAIL_CLOSED",
                              "PLAN_BOUND_SEVEN_STEP_OPERATOR_GUIDE",
                              "STATE_AWARE_GUIDE_WITH_CANONICAL_SHA",
                              "OPT_IN_MANUAL_TELEMETRY_PROPOSALS_ONLY",
                              "G241_REAL_CHROMIUM_CSV_LOST_REPLY",
                              "G241_RELOAD_MANUAL_ID_GET_RECOVERY",
                              "G241_JSON_DOWNLOAD_CONSENT",
                              "G242_REAL_BROWSER_LOCAL_NL_TO_TYPED_CSV",
                              "G242_COMPOUND_WRITE_INTENT_FAIL_CLOSED",
                              "G243_OPTIN_REDACTED_CSV_HISTORY_GET_ONLY",
                              "G244_EXPLICIT_CREATE_ONLY_FULL_LOCAL_REPORT",
                              "G245_REAL_REPORT_SHA_OK_AND_TAMPER_CONFLICT",
                              "G246_REVIEWED_OUTPUT_SCOPE_REUSE_REFUSED",
                              "G248_REAL_CHROME_SCOPED_VERSION_REVIEW_OPTIN",
                              "G254_ONE_LINE_VERSION_SCOPE_REAL_CHROMIUM_E2E"],
                    "real_nas_verified":False,"trial_started":False,"release_gate":"HOLD"
                }
        finally:
            if browser is not None:
                with suppress(Exception):browser.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


def main():
    try:
        result=run_browser()
    except Exception as exc:
        # A browser that actually launched but failed its assertions is a
        # failed E2E, not a success and not the same as missing dependencies.
        detail=str(exc)
        blocked="ERR_BLOCKED_BY_ADMINISTRATOR" in detail
        # Report reproducible code location + first error line only. No browser
        # headers, bearer token, customer paths or raw request payloads.
        frames=[frame.lineno for frame in extract_tb(exc.__traceback__)
                if Path(frame.filename).name == Path(__file__).name]
        first_line=detail.splitlines()[0][:160] if detail else "UNKNOWN"
        if any(word in first_line.lower() for word in
               ("bearer", "authorization", "token", "cookie")):
            first_line="REDACTED"
        result={"status":"REAL_BROWSER_E2E_BLOCKED_BY_ENVIRONMENT" if blocked
                else "REAL_BROWSER_E2E_FAILED",
                "reason_type":type(exc).__name__,
                "failure_source_line":frames[-1] if frames else None,
                "reason_first_line":first_line,"release_gate":"HOLD"}
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))
    return 0 if result["status"]=="REAL_LOCAL_BROWSER_E2E_PASS_NOT_NAS" else 2


if __name__=="__main__":
    raise SystemExit(main())
