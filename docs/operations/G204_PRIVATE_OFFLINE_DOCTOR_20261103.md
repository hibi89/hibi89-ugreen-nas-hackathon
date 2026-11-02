# G204 isolated Windows offline readiness package (2026-11-03 KST)

## Goal and approach

Remove unnecessary user friction before the genuine official Uliya Creator action while retaining explicit owner authorization for all private-model input or tool execution. Existing G203 ZIP requires manual Python invocation; G204 is an **additive owner-private ZIP**, not a modified G203 original and not a submission artifact. Compared (A) embedding an auto-executing Codex workflow vs (B) a double-click **offline preflight only**. Selected B to avoid model/network/API costs, unexpected data transmission, permissions changes and false provenance.

## Exact byte evidence

- Read original G203 ZIP at SHA256 `92bbd9657cfdcc80c997f2dcfad6cc80f7612e1908b757b5b3ba7b04b11df44d`.
- Generated `UGREEN_G204_PRIVATE_CREATOR_LOCAL_DOCTOR_NOT_SUBMITTED.zip` (101,895 bytes; SHA256 `cb3f80ec1174b6513e2fd3dbf43eab457b8312f83e32c8b07587d4897221e8c9`; 35 entries, full archive CRC PASS) containing **all 32 unchanged original G203 members** and three new files: `RUN_G204_OFFLINE_READINESS_ONLY.cmd`, `tools/g204_offline_readiness.py`, `G204_README_FIRST.md`.
- Offline Python test extracted the actual new package into a fresh directory and executed its exact doctor program with Python 3.13.5: source hashes G188/G157/Kit 3/3 PASS, 26 official installed Kit files byte-identical to original archive, G188 ZIP/member integrity PASS, original source unchanged, `local_preflight=PASS`, `codex_path_detected=false`, process exit 3 as designed for missing Codex PATH. No generated `output` directory or external side effects. This **does not** establish Windows `.cmd` execution or user Codex discovery; Windows testing remains NOT_RUN.
- Official UGREEN Starter Kit states Codex is an accepted assistant and official Creator invocation is required. Current VS Code Agent Skills documentation confirms project `.agents/skills/` is an accepted Codex Skill directory. This confirms placement in principle only, **not** runtime discovery or official Creator usage. See https://ai.ugreen.com/pages/hackathon-starter-kit and https://code.visualstudio.com/docs/agent-customization/agent-skills.

## Status, security and next gate

- Neither G203 nor G204 package was uploaded to public GitHub or Devpost. G188/G157/Kit remain unchanged in private Library. G204 is temporary user-downloadable private workspace; do not embed in public repo or claim permanent storage.
- **Official Creator NOT_RUN, official first-party Checker NOT_RUN, registered Expert/NAS NOT_RUN, Devpost NOT_SUBMITTED; release HOLD, NAS technical NO-GO.** Do not infer genuine creator proof, authenticated model use, private-source sharing authorization, source rights or Windows CLI presence from an offline doctor.
- Next is genuine owner-local Windows readiness check by double-clicking `RUN_G204_OFFLINE_READINESS_ONLY.cmd`, then after separate explicit consent manually opening Codex in the private project and confirming installed `$uliya-skill-kit` recognition before sending sensitive reference contents. New generated candidate / true tool receipt must be reviewed, and independent Checker, final owner pair approval and Devpost later require distinct approvals. No NAS 3h trial use.
- Latest prior G201 feature SHA `dc05fe8f60cff055a261f7e3536ab6576951065a` Linux 1440 PASS/0 FAIL/16 SKIP and Windows SUCCESS. G204 makes no GitHub functional changes; only this status documentation. This docs SHA and closeout CI must be verified independently. Historic ~90% completion estimate not updated.
