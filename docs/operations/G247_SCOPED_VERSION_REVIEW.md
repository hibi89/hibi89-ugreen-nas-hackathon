# G247 FlowPilot 3.0 — bounded version review, operator guide

Status: Verified on disposable local files at GitHub SHA f316646fa5decdc9043d596f92a5417b8257f8ac. This is an owner-local Python CLI capability, NOT the officially registered Uliya Skill, NOT NAS validation, and NOT integrated into the legacy two-template web dashboard. RELEASE HOLD.

## Purpose and explicit scope

The third compiler template, scoped_version_review_v1, maps ONLY the exact Korean or English requests "버전 비교해줘", "문서 버전 충돌 확인해줘", "review versions", or "compare versions" to a read-only, bounded four-stage plan: metadata inventory, exact owner-named version comparison, owner decision required, and redacted evidence. Unknown/compound/write/transfer requests are refused, not rewritten into a broader goal. It never decides which version is final or uploads anything.

The owner must separately decide that the exact folder is a trusted LOCAL, non-network directory. This tool cannot prove mapped drives are not NAS mounts and is not safe for concurrently modified, adversarial Windows folders. Do not use real client credentials, source repositories containing secrets, private keys or uncontrolled directories.

## Safe preview (no local-folder access)

From the repository root with Python 3.11 installed:

    python tools/flowpilot_task_compiler.py --goal "review versions" --compile-only

Inspect the four-node typed plan and the explicit NOT NAS / HOLD markers before authorizing any metadata read.

## Explicitly scoped version review

Use a disposable owner-controlled LOCAL test folder containing two version candidates (for example release/final.pdf and release/final_v2.pdf). This is a user-side command for later, not a claim the assistant accessed user files:

    python tools/flowpilot_task_compiler.py --goal "review versions" --root "<TRUSTED_LOCAL_FOLDER>" --required "release/final.pdf" --candidate "release/final.pdf=release/final_v2.pdf"

Without approval, the result is WAITING_LOCAL_METADATA_APPROVAL, and selected folder metadata is not accessed. Inspect the exact folder, required path and competitor before opting in:

    python tools/flowpilot_task_compiler.py --goal "review versions" --root "<TRUSTED_LOCAL_FOLDER>" --required "release/final.pdf" --candidate "release/final.pdf=release/final_v2.pdf" --approve-local-metadata

The tool only calls the established G62 lstat-based metadata inspector for explicitly named candidates (up to its fixed bounds). It opens no file bodies. It reports redacted indices and PRESENT / MISSING / NOT_CHECKED / VERSION_REVIEW, and no source path, relative filename, original contents, inferred latest version, live NAS status or external identity. If an alternate exists, VERSION_REVIEW requires an owner decision. Missing or incomplete results never become READY.

## Safety and support boundary

- Changing the folder, required paths, candidate mapping, goal or approval requires a new invocation. No automatic background scan, upload, file deletion, renaming, data write or NAS Expert calls.
- Traversal, restricted targets, duplicate and excessively large scopes, symlink/reparse uncertainty or unsupported requests refuse or return NOT_CHECKED. Metadata scanning does not certify concurrent file consistency or Windows drive provenance.
- The existing localhost dashboard's two-template synthetic-artifact engine intentionally refuses this new CLI-only template until a separately validated end-to-end UI/receipt adapter exists. Other existing dashboard features are unchanged.
- Test evidence: GitHub run 41852929264 Linux 1583 PASS / 0 FAIL / 16 SKIP and Windows PASS; browser 41852929307, readiness 41852929418, master 41852929400 and closeout 41852929212 all SUCCESS.
- Official Skill ZIP/PDF, Uliya v0.7.3 Kit, Owner Creator/Checker permissions, NAS trial and Devpost submission remain unaffected and NOT_RUN. Final submission requires a separate owner release decision.
