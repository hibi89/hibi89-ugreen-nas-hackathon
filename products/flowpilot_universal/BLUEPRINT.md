# FlowPilot Universal final-product design and P50 traceability

Source: central approved product brief at hackathon-command-center-2026/kmong-productization/docs/commercial/KMONG_3_NEW_PRODUCTS_20261112.md. This separate product MUST NOT be conflated with the UGREEN NAS Skill or its contest progress.

## Competing designs and choice
A. Depend on UGREEN Uliya Expert/Skill: potentially faster NAS integration but cannot promise other NAS/Windows compatibility, requires NAS/Expert authorization, creates dependency on a competition-specific runtime and unknown licensing. Hardware access and customer suitability remain untested.
B. Independent Python 3.11 local scanner of operator-authorized PC/USB/OS-mounted SMB path: no third-party runtime/API, no monthly hosting, portable contract and lower security exposure, but GUI/installer/real UNC SMB validation cost remains. **B selected for P50** (matches central brief). No automated NAS operation and no silent discovery.

## Final intended product and traceability (no retroactive percentage grant)

| ID | Final customer requirement | P50 implementation | Evidence / remaining acceptance |
| --- | --- | --- | --- |
| F01 | Explicit consent and scoped local/SMB source | Root CLI argument and regular directory preflight | Source engine.py; real SMB/permissions NOT_RUN |
| F02 | Template-based required delivery file matching | Schema v1 requirements manifest with strict relative paths | tests missing, traversal, collision PASS; GUI template library NOT_BUILT |
| F03 | Byte-level SHA-256 integrity check | fd-bound hashing with best-effort before/after metadata check | tests ready/mismatch PASS; cross-device race/immutable snapshots NOT_PROVEN |
| F04 | Duplicate/version conflict review | Exact-content duplicates, filename version candidates | tests duplicate/version PASS; semantic versions/collaboration NOT_BUILT |
| F05 | Source safe/no unauthorized mutations | read-only filesystem operations; links/reparse/special entries -> INCOMPLETE; scan cap | tests link, limits, unreadable PASS; Win junction/race hardening NOT_DONE |
| F06 | Delivery evidence | Local create-only JSON + escaped static HTML, no network | tests report/CLI/escaping PASS; customer-facing PDF and consented history NOT_BUILT |
| F07 | General user workflow and error recovery | Deterministic CLI statuses READY/BLOCKED/NEEDS_REVIEW/INCOMPLETE | customer GUI, scan resume, selective re-check NOT_BUILT |
| F08 | Production Windows portable delivery | Python standard-library source prototype only | EXE, packaging, signing, Win10/11 customer device NOT_RUN |
| F09 | Authorized actual PC/USB/SMB hardware acceptance | No physical hardware touched | real Windows UNC share, NAS models and high-volume test NOT_RUN |
| F10 | Commercial user acceptance and legal delivery | no sale and no permission external transfer | EULA, copyright/3rd-party reviews, support, customer pilots, seller GO NOT_DONE |

**P50 engineering gate (internal, scoped):** F01-F06 have proof at synthetic Linux and Windows Python3.11 tests. This is NOT official 50% of final blueprint. The official completion percentage is **UNASSESSED** under OWNER-FINAL-BLUEPRINT-100, because a complete 100-point owner-approved item weight table and real end-to-end acceptance evidence have not been approved. Do not convert number of tests, internal stage names, or code lines to final percentage.

## Planned stage gates (not retroactive credits)
- P50: contract, independent offline core, fail-closed output, focused deterministic tests (implemented, synthetic only).
- P70: actual user GUI, guarded local report history/backup, large folder interruption and resume, scan stabilization.
- P85: Windows EXE installer/portable signature, full negative security regression and user documentation.
- P95: real Windows10/11 local USB+permissioned SMB NAS from multiple vendors, independently checked report parity, business customer use cases.
- P100: verified consent/rights/contract, complete final blueprint owner-approved scoring, support/refund/license and real user acceptance, explicit commercial release GO.

Nothing here authorizes remote SMB credentials, external uploads, NAS scripts, paid subscriptions, production deployment or customer data access. Customer filenames in HTML/JSON are sensitive; output stays local only.
