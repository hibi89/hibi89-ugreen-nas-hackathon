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

from flowpilot_local_backend import Backend, create_server


def run_browser():
    try:
        from playwright.sync_api import sync_playwright
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
                try:
                    browser=playwright.chromium.launch(headless=True,timeout=10000)
                except Exception:
                    binary=next((shutil.which(name) for name in
                                 ("chromium","chromium-browser","google-chrome","msedge")
                                 if shutil.which(name)),None)
                    if binary is None:
                        return {"status":"REAL_BROWSER_NOT_VERIFIED",
                                "reason":"BROWSER_BINARY_UNAVAILABLE","release_gate":"HOLD"}
                    browser=playwright.chromium.launch(executable_path=binary,
                                                       headless=True,timeout=10000)
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
                page.wait_for_function(
                    'document.getElementById("connection-status").textContent.includes("로컬 연결 확인")')
                assert page.locator("#token").input_value()==""
                page.locator("#create").click()
                page.wait_for_function(
                    'document.getElementById("workflow-state").textContent === "PLANNED"')
                page.locator("#plan").click()
                page.wait_for_function(
                    'document.getElementById("plan-hash").textContent.includes("검증한 계획 SHA-256")')
                assert page.locator("#approve").is_disabled()
                page.locator("#test").click()
                page.wait_for_function(
                    'document.getElementById("workflow-state").textContent === "TESTED"')
                page.locator("#plan").click()
                page.locator("#synthetic-consent").check()
                page.locator("#approve").click()
                page.wait_for_function(
                    'document.getElementById("workflow-state").textContent === "APPROVED_SYNTHETIC"')
                page.locator("#run").click()
                page.wait_for_function(
                    'document.getElementById("workflow-state").textContent === "COMPLETE_LOCAL_SYNTHETIC"')
                page.locator("#audit").click()
                page.wait_for_function(
                    'document.getElementById("output").textContent.includes("LOCAL_CHAIN_INTACT")')
                page.locator("#evidence").click()
                page.wait_for_function(
                    'document.getElementById("output").textContent.includes("LOCAL_SYNTHETIC_EVIDENCE_VERIFIED_NOT_NAS")')
                with page.expect_download(timeout=8000) as transfer:
                    page.locator("#report").click()
                download=transfer.value
                saved=folder/"browser-fixture.csv"
                download.save_as(saved)
                assert saved.stat().st_size>0
                assert sha256(saved.read_bytes()).hexdigest() in page.locator("#output").inner_text()
                page.locator("#required").fill("README.md\nmissing.pdf")
                page.locator("#meta-preview").click()
                page.wait_for_function(
                    'document.getElementById("metadata-summary").textContent.includes("WAITING_APPROVAL")')
                assert page.locator("#required").input_value()==""
                assert page.locator("#meta-approve").is_disabled()
                page.locator("#metadata-consent").check()
                page.locator("#meta-approve").click()
                page.wait_for_function(
                    'document.getElementById("metadata-summary").textContent.includes("LOCAL_METADATA_BLOCKED")')
                page.locator("#token").fill("short")
                page.locator("#connect").click()
                page.wait_for_function(
                    'document.getElementById("create").disabled === true')
                assert page.locator("#token").input_value()==""
                if errors:
                    raise RuntimeError("BROWSER_CONSOLE_OR_NETWORK_ERROR")
                context.close()
                return {
                    "status":"REAL_LOCAL_BROWSER_E2E_PASS_NOT_NAS",
                    "checks":["DOM_RENDER","TOKEN_CLEAR","PLAN_TEST_APPROVE_RUN",
                              "AUDIT_EVIDENCE","CSV_SHA_DOWNLOAD","METADATA_CONSENT",
                              "INVALID_REAUTH_CLEARS_AUTH"],
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
        result={"status":"REAL_BROWSER_E2E_BLOCKED_BY_ENVIRONMENT" if blocked
                else "REAL_BROWSER_E2E_FAILED",
                "reason_type":type(exc).__name__,"release_gate":"HOLD"}
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))
    return 0 if result["status"]=="REAL_LOCAL_BROWSER_E2E_PASS_NOT_NAS" else 2


if __name__=="__main__":
    raise SystemExit(main())
