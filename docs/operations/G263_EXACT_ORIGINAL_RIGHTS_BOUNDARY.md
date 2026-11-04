# G263 — original G226 Markdown provenance and limited rights boundary
Date: 2026-11-05 KST. No official Creator or NAS run. Release HOLD.

## Motivation and design options
Prior G262 establishes first-party static Checker success but cannot establish license clearance or official Creator provenance. Option A, presume all rights from static pass, rejected as unsupported. Option B, selected: independently bind original package bytes/disclosure to publicly verifiable terms and use a narrow fail-closed offline verifier. No private Skill text or vendor Kit was committed.

## Independently reviewed official sources
- UGREEN Devpost rules: https://ugreenhackathon.devpost.com/rules — entrant-owned new Skill, official Skill Creation Tool, third-party rights, disclosure; source instructions alone do not prove official Creator invocation.
- UGREEN NAS Agreement (updated Jan 29 2026): https://ai.ugreen.com/pages/useragreement — limited revocable use, not a blanket vendor SDK redistribution license.
- OpenAI Terms of Use: https://openai.com/ko-KR/policies/terms-of-use/ — OpenAI assigns output rights to user as between those parties under applicable law/terms, without guaranteeing unique copyrighted originality or absence of third-party rights. User account-specific terms not verified.

## Executed evidence
- Exact original private G226 ZIP SHA256: fcd628b86ea55b1b1923256d088d21f8bb28642df0839df8353c139a2e6fa803
- Exact first-party official Kit 0.7.3 SHA256: cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3
- tools/flowpilot_g263_rights_boundary.py verifies authentic exact ZIP and all four original Markdown SHA256 hashes; rejects extra ZIP files, incorrect names/hashes, non-UTF8, executable fenced script, duplicate/traversal/symlink paths, and checks disclosure of principal work, AI authoring and missing rights. It does not prove noninfringement for every paragraph.
- Actual owner-private original+Kit input: exit 0, status EXACT_ORIGINAL_MARKDOWN_AND_DISCLOSURE_BOUND_NOT_LICENSE_CLEARANCE; four matching files, no vendor whole Markdown copied, no executable/SDK bundled, no network, release HOLD; private evidence SHA256 77afc43c02f043c9085ee378a68cd26a38b395e5a3475492c635ac864b4c776d.
- 10/10 local Python 3.13 synthetic tests PASS, 0 FAIL; separate exact-original input exit 0. Remote GitHub code/test blob identity checked against locally executed bytes.
- Exact new SHA GitHub Actions Ubuntu/Windows NOT VERIFIED at this checkpoint.

## Scoring and limits
This is one previously unearned official rights evidence milestone candidate, but score stays 70/100 (official 10/15) until acceptance requirements including CI are met. No legal clearance, creator invocation, rights attestation, actual registered Expert/NAS proof, release or submission. Do not double-credit prior source-only checks. No additional local 60/60 credit.

## Rollback / asset protection
Only verifier + synthetic tests + this documentation changed in public branch; canonical Skill, G226/G221 private owner source, official Kit, PDFs, databases and credentials unchanged. Ordinary git revert of G263 commits, no forced history changes. External provider calls, NAS activation and Devpost remain separately approval-gated.
