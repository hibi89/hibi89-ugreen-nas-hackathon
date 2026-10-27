> **G46 2026-10-27 CORRECTION:** Earlier G45 PDF SHA was incorrectly recorded as 9832ae8d291b365afb2c026448aca4b7a83edd01fc5ce83eb348e8c5eae2f122; re-read original mounted G45 PDF SHA is 0eb7c28aeea1d9b6c4a13a92b0c0c6086a32a9e9a89bcdb5b9936ad95c4049a6. G45 also paraphrased several official Q headings; corrected G46 separate 1-page PDF uses exact 10 official strings from tools/check_round1_proposal.py, 359 answer words, local SHA f7225b229b3ce35999eb384f5c3857eaa22e8c49851bda51047330d1de7c8b1b. ZIP remains exact same source SHA and ZIP hash as G45. Both new GitHub CI results STILL_UNVERIFIED. G45 official checker workflow accidentally ran nonexistent test_g45_delegate_semantics.py and silently risked running zero tests; G46 repair now enforces >=34 test discovery and successful results. Do not claim official Creator or NAS PASS. This file retains historic G45 record and G46 correction.

# G45 NAS FlowPilot – Round 1 new-candidate owner-review package

2026-10-27 KST. Source branch lead/ugreen, prior head d85557439de2c528cb531c759cc527ee4d6ac34c. This is a PRE-SUBMISSION REVIEW DRAFT, NOT an official Devpost receipt.

## Artifacts locally independently checked
- Original new FlowPilot candidate: skill/flowpilot-nas/SKILL.md; raw UTF-8 bytes 7495; SHA256 985713d709aa36ad3e590557aac242be860716834f31eb27ff460bee960184b0. Matched actual GitHub git-blob identity bb7d67dfcaaea5969f2d6aa7738a8eaa67e233e9.
- Owner-review PDF: 1 rendered A4 page, all 10 official Q/A extracted, 359 substantive answer words (<500); local output SHA256 0eb7c28aeea1d9b6c4a13a92b0c0c6086a32a9e9a89bcdb5b9936ad95c4049a6.
- Owner-review ZIP: one and only one file flowpilot-nas/SKILL.md, byte-for-byte identical to canonical GitHub candidate; local ZIP SHA256 973ec305f479ba88963e8541ebd9e34de1394ca4e5cf76f2ee102ad46c823919.
- LOCAL generated PDF, ZIP and manifest are ChatGPT working-container deliverables. Never claim the same PDF hash for a future CI build unless verified; ReportLab/PDF metadata may vary.

## Changes made
- Added JSON source for ten English proposal answers and disclosure.
- Added Python-only development PDF/ZIP builder (NOT inside Skill ZIP).
- Added G45 separate owner-review GitHub workflow; tests 10 PDF questions, word limit, source-bound exact ZIP, offline FlowPilot tests, then retains 7-day preview artifact.
- Added G45 separate first-party pinned Uliya checker workflow adapted from verified G36 isolation but TARGETING THE EXACT NEW FLOWPILOT SKILL. It downloads only a pinned public vendor archive, verifies digest, executes checker under --network none and read-only mount, and fails if diagnostics are not clean. No official result is claimed until this workflow is observed.

## Submission gate
UGREEN Round 1 requires new official UGOS/Uliya Creator skill and matching SKILL.md ZIP plus 10 official Q/A PDF <=500 substantive words. At Round 1, real NAS runtime is NOT required; Round 2 finalist later must run same project on assigned real NAS.
Skill candidate has NOT been executed through official Creator. New first-party checker workflow is staged and awaiting run verification; this cannot substitute for official Creator provenance.
Original G36/G37 PDF, ZIP and Skill are preserved and must not be silently presented as FlowPilot.
Do not include extra scripts, binaries, third-party SDK code or user data in contest ZIP.
Rights statement in PDF is a disclosure draft, not a legal warranty. Technical support described possible own-work license choices; entrant must review and approve final exact ZIP and PDF before Devpost.
No real NAS, registered Agent calls, external file access, paid API, user uploads, Devpost publication or Production deployment performed.

## Next concrete work
1. Read actual G45 Actions logs/diagnostics and verify both new workflows; fix real failures only.
2. If checker status static-pass, separately arrange official Creator use on exact FlowPilot candidate. Do not inherit G36 proof.
3. Entrant reviews the 10 Q/A text, AI disclosure, rights, unsupported runtime claims, and exact candidate checksum, then approves or requests changes.
4. After approved revised bytes, rerun validation and package checks; only then user-authorized Devpost submission.

Official sources: https://ugreenhackathon.devpost.com/rules and https://ugreenhackathon.devpost.com/resources
