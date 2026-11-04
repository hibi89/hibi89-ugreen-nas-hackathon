## G264 official SkillHub policy correction (2026-11-05 KST)

The G263 general UGREEN NAS User Agreement was **not** the directly relevant SkillHub publishing contract. The official hackathon Starter Kit links to the current `SkillHub User Agreement` and `UGREEN SkillHub Content Submission and Publication Standards`; separate Uliya runtime terms also apply. Source:
- https://ai.ugreen.com/pages/hackathon-starter-kit
- https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-user-agreement
- https://api.ugnas.com/api/system/v1/ua/agreement/page?acceptLanguage=en-US&agreementCode=skillhub-publish-audit-spec
- https://ai.ugreen.com/pages/uliya-user-agreement

Official first-party terms allow independently owned developer Skill content subject to third-party rights, require an appropriate license label and a license grant to the platform on upload, and expressly state a unilateral ownership declaration does NOT itself prove ownership. The first-party static Checker cannot replace rights evidence. A supported Creator execution is still unproven. No upload or publisher license was granted.

G264 corrects `OFFICIAL_SOURCE_PAGES` in `tools/flowpilot_g263_rights_boundary.py`, adds explicit output flags `skillhub_publisher_rights_attestation_verified=false`, `skillhub_compatible_license_choice_verified=false` and `platform_static_checker_is_license_clearance=false`, and adds a source-list regression test. Original G226+first-party Kit offline CLI pass; local Python 3.13 unit **11 PASS / 0 FAIL**, full Linux/Windows GitHub Actions for exact new source not verified. Source Git blob `2833c53926ffe51f1b5eeb3bc9609792a7540167`, test Git blob `1dac5216b30afd0ce3fd20eb7a82263c907cd810`; owner-private evidence SHA256 `b78397ae1e0341c89224910ae9e5895c6810a86c142bbb2fa77fa45ccff513cc`, not uploaded to public repo.

**No full-product point earned yet:** official 10/15, full product 70/100; Creator/rights 5, registered native/NAS 20, final release 5 remain. Release HOLD, NAS NO-GO. This corrigendum supersedes the G263 source list/assumed applicable agreement but does not alter its original-source acceptance caveats.

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
