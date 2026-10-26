# G37 — G36 first-party static-pass matched Round1 owner-review artifact candidate (2026-10-26)

This is **DRAFT ONLY; NO SUBMISSION**. The new G37 builder [source](../../tools/round1_g37_release_parity.py) preserves all previous G29/G32/G34 PDFs, ZIPs, Skill sources and official-checker receipts. It strictly verifies the G36 source SHA256 `e4e45dea7f2ca22a37c2c3803ed12d6b9914c7ca4686d9b891976ba1481610a4`, 14,522 bytes, and machine-readable G36 first-party `static-pass` 0/0/0 run 40311253113 before writing any candidate.

## Verification plan and current state
- Separate G37 proposal with 10 original required English question titles, Q8 truthfully reflecting independently verified G36 static pass and still unknown live NAS/agents; explicit AI assistance, vendor kit and offline libraries, uncertain local/cloud data flow; <=500 substantive answer words.
- PDF generated with unchanged ReportLab renderer and strictly parsed by pypdf for entire 10 Q/A text plus four disclosures, <=1MB, **one page**. Additional PyMuPDF scan checks page blocks lie inside page boundaries; emits a PNG for human visual inspection.
- Deterministic ZIP with **exactly one `projectready-nas/SKILL.md` entry** containing byte-for-byte official checked G36 source, <=10MB. SHA256 manifest and original JSON/Markdown output with owner review watermark; no NAS, secrets, vendor kit scripts or third-party binary code in ZIP.
- [G37 GitHub Actions](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/workflows/g37-round1-owner-review.yml) includes six G37 regressions, synthetic full suite as a separate workflow, and visual raster generation. Its first run found a receipt validation field mismatch and an over-specific test assertion. Both were changed; **corrected CI outcome pending evidence**.
- Past verified G36 vendor checker result applies ONLY to exact G36 bytes. Actual G37 PDF/ZIP hashes **must be captured from successful CI before release**.

## Unchanged external gates
Rights and third-party UGREEN license **NOT CLEARED**, entrant original authorship and final editorial review **PENDING**, real registered expert/NAS/runtime **NOT_RUN**, SkillHub/Devpost **NOT SUBMITTED**. Round1 structure does not establish official eligibility. No unapproved external data or expense.

## Ledger
Historic 24-day 2 DONE /12 PARTIAL /3 BLOCKED /7 NOT_STARTED; Oct26 G1 runtime 0% BLOCKED, base 1.5h + separate reserve 1.5h, actual time unknown. G37 part of originally planned UGR-D16/D17 advance work, not new schedule completion.
