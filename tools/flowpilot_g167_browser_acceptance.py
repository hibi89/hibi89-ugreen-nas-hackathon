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
                        executable_path=binary,headless=True,timeout=30000)
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
                page.locator("#create").click()
                expect(page.locator("#workflow-state")).to_have_text("PLANNED")
                page.locator("#guide").click()
                expect(page.locator("#output")).to_contain_text("합성 전용 7단계 운영 가이드")
                expect(page.locator("#output")).to_contain_text("7. 운영 전 승인 게이트")
                expect(page.locator("#output")).to_contain_text("NAS / Uliya / Docker 실행 검증 아님")
                page.locator("#plan").click()
                expect(page.locator("#plan-hash")).to_contain_text("검증한 계획 SHA-256")
                assert page.locator("#approve").is_disabled()
                page.locator("#test").click()
                expect(page.locator("#workflow-state")).to_have_text("TESTED")
                page.locator("#plan").click()
                page.locator("#synthetic-consent").check()
                page.locator("#approve").click()
                expect(page.locator("#workflow-state")).to_have_text("APPROVED_SYNTHETIC")
                page.locator("#run").click()
                expect(page.locator("#workflow-state")).to_have_text("COMPLETE_LOCAL_SYNTHETIC")
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
                              "PLAN_BOUND_SEVEN_STEP_OPERATOR_GUIDE"],
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
