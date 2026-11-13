# FlowPilot Universal — 2026-11-14 F08/F09 Windows EXE and F10 zero-cost commercial rights preflight

## Fixed final scope, status and technical evidence
- The owner's entire existing F01–F10 blueprint is the denominator, unchanged. User target ≥85%; no unapproved weights, deleted requirements, or retrospectively gamed score. **Official final completion: UNASSESSED, 85% NOT CERTIFIED, [작업중], RELEASE/SALE HOLD.**
- Tested feature SHA: `e8bc4f318087bd83634f9f177e73fbc87e43a95f`; pre-change safe restore SHA `6fbb0163c891dbe25f8408fc6a724688018a1224`.
- [Source CI #43511163767](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43511163767): **Windows 111 PASS / 0 FAIL / 0 SKIP**, **Linux 104 PASS / 0 FAIL / 7 NTFS-Windows-only SKIP** (111 total), portable8 rerun/OS, real Tk5/OS, compileall, 2/2 SUCCESS.
- [Windowed EXE build/install/relocation #43511163790](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43511163790): PyInstaller6.22.3 Windows Python3.11 `--onedir --windowed`, bundled app `--self-test` **EXIT0**, SHA verified full ZIP relocated and `--self-test` **EXIT0** without developer Python PATH, safe temporary install/verify/uninstall **PASS** with unrelated-file deletion refused. Self-test now executes `--field-trial` through the *packaged* EXE logic on synthetic files (3 rounds) including rejected no-consent path; 2 additional unit regressions verify entrypoint plus null stdio. **Not signed, uploaded, released or run on customer hardware**.
- This is real functional F08/F09 Windows executable compatibility progress, not customer F09 hardware or F10 legal acceptance.

## Owner-operated local full-rehash trial — only on authorized existing folder
The Windows portable folder must contain all bundled files, not just `FlowPilotUniversal.exe`. From an explicitly authorized environment, the existing `desktop_entry.py` Windows EXE supports:
```powershell
$exe = "C:\PATH\FlowPilotUniversal\FlowPilotUniversal.exe"
$argv = @("--field-trial", "--root", "C:\AUTHORIZED-SOURCE", "--manifest", "C:\APPROVED\requirements.json", "--output", "C:\EXISTING-SEPARATE-OUTPUT", "--medium", "pc", "--consent")
$proc = Start-Process -FilePath $exe -ArgumentList $argv -Wait -PassThru
$proc.ExitCode
```
Replace placeholders. `--medium` = `pc`, `usb`, or `smb` is operator attestation only; tool **does not prove** a physical USB/NAS or authorization. The `--windowed` EXE has no console output: inspect create-only `flowpilot-field-trial-*.json` in output. 0 indicates three *local* stable SHA scans, **not field buyer acceptance**; 2 signals HOLD. For paths with special quotation/space characters, use the Python CLI with a shell that preserves arguments or another approved launch mechanism; do not weaken path validation. No automatic SMB share creation, account changes, mounts, credential collection, external upload or NAS actions. The existing README Python CLI is also supported.

## F10 commercial dependencies: factual licenses vs unresolved seller rights

| Component | Verified official position | Remaining release obligation |
|---|---|---|
| **PyInstaller 6.22.3** | [Official license](https://www.pyinstaller.org/en/stable/license.html): commercial bundles allowed under GPL exception; bundled dependencies must separately comply | Review actual frozen dependency set and inherited notices; cannot treat exception as blanket license |
| **ReportLab OSS 4.4.9** | [Official developer FAQ](https://docs.reportlab.com/developerfaqs/): OSS toolkit BSD, including commercial software | Inspect installed wheel license, copyright and packaged extra components; final NOTICE/rights review |
| **Naver Nanum** | [Naver official license](https://help.naver.com/service/30016/contents/18088?osType=PC): commercial use allowed under OFL 1.1, redistribution subject to full font-license terms | CI installs open Nanum OS font only; **no font shipped with app**. If redistributed later include exact OFL + copyright notices and check modified-name restrictions |
| **Windows Malgun Gothic TTF** | OS-local font discovered by PDF optional runtime; no font binaries shipped | Embedding/distribution rights and actual generated-PDF license compliance **NOT VERIFIED**; do not assume Windows installation authorizes repackaging |
| **Python / Tcl-Tk / bundled transitive dependencies** | Runtime and libraries required by PyInstaller; current workflow does not separately inventory every bundled license | Produce exact final wheel/binary SBOM and preserve all required license files before any public sale or downloadable release |
| **First-party product source** | Public repository does not by itself establish seller ownership or customer license | Ownership, EULA, warranty, data retention, refund/support terms and sales-channel rules remain OWNER/LEGAL REVIEW |

The user authorized **only additional-cash-cost-zero commercialization preparation**. Free checks, docs, quality tests and candidate packaging are within scope. No certificate purchase, paid API, change to actual customer PC shares/rights, real NAS access, customer data upload, public GitHub Release, signing or sale is authorized by this preflight.

## Residual acceptance and continuation
- F01–F08 technology/packaging remains supported by hosted synthetic tests, not blanket buyer acceptance.
- **F09:** verify on owner-approved physical Win10/11, real USB, and owner-authorized SMB NAS from two distinct vendors; ACL/locked files/high volume/race/long-path and 3-pass audit source/report parity must be measured. Existing PC-only SMB tests (if any) cannot replace the physical NAS requirement.
- **F10:** final proprietary/open-source copyright, font embedding, notices, code signing/SmartScreen or documented unsigned distribution risk, installation/uninstall/customer-safety, EULA/privacy/support/refund and independent user acceptance.
- The approved original F01–F10 100-point requirement scoring and evidence remain missing; do not calculate an invented 85% from test counts, F08/F09 code milestones or the number of rows in this document. Preserve `[작업중]`, RELEASE/SALE HOLD and historic registration records.
