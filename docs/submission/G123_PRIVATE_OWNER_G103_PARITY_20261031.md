# G123 G103 private Round 1 artifact byte parity and release gate — 2026-10-31 KST

**Current rule source:** https://ugreenhackathon.devpost.com/rules and https://ai.ugreen.com/pages/hackathon-starter-kit (checked 2026-10-31). Round 1: exactly 10 substantive English answers, <=500 words; PDF <=1 MB; Markdown-only SKILL.md ZIP <=10 MB including an <=1 MB/file and <=100 files; only documented Uliya registered Experts, no custom executable code in Skill; no NAS runtime evidence required.

## Evidence and exact original (not redistributed)
The private owner-held G103 outer review bundle is not in public GitHub. Historical exact pins:
- G103 SKILL.md f940bcd884b83d80fbecf533caee7d492488c274e1d3eab2b99b034b92428e15
- G103 inner ZIP 1496103b5c1b15da113867ed0cab57ad1e2dab0be80c2f06fd049cac359bf11b
- G103 proposal PDF b775510605be963e38ad05057a9cb1edcc5e79a6b1e3417e302af4887aaf6858

On 2026-10-31, the owner-held private outer bundle was read from the model's available runtime, WITHOUT changing or uploading it; ZIP CRC and manifests matched the three original SHAs and sizes, and PDF 1 page was actually rendered for visual reading. Ten official answers were visible; manual Python token checks yielded 347 whitespace-separated words and 365 conservative ASCII tokens, both <=500. The older source labels 357 words; this is an admissible variation between counting rules, not a new assertion that the printed 357 was independently reproduced exactly. Actual PDF text was inspected separately with PyMuPDF, not by the new stdlib checker.

## Code and boundaries
New tools/flowpilot_round1_candidate_parity.py accepts one explicitly selected **local owner-review ZIP**, verifies all four expected outer files and exact G103 SHA pins, checks ZIP metadata/CRC/limits, inner Markdown-only single Skill, safe frontmatter, proposal 10 answers, conservative word upper bound, source/manifest checksums, disclosure parity and fail-closed non-submitted/unverified flags. No archive extraction, network, NAS or Uliya calls; no owner content or filesystem path printed. Synthetic tests may inject fake hashes, but are tagged SYNTHETIC_TEST_PROFILE_ONLY. A matching private bundle gives G103_BYTE_PARITY_AND_STRUCTURE_PASS_NOT_OFFICIAL with release_gate HOLD. The script does NOT parse/visually audit the PDF itself; its PDF inspection is signature/length/hash and optional actual-byte match to G103 only.

Command: python tools/flowpilot_round1_candidate_parity.py --bundle OWNER_LOCAL_G103_REVIEW.zip
Tests: python -m unittest discover -s tests -p 'test_flowpilot_round1_candidate_parity.py' -v
CI: exact-source Linux + Windows hosted full regression.

## Outstanding external / human gates
G103 official first-party 0.7.3 Checker requires already authorized genuine vendor kit SHA cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3 and approved executable environment. Prior binary download attempts failed. No official checker run claimed here. Registered Expert and NAS not required Round 1; rights and license, owner release approval and Devpost submission still HOLD. The private original must not be committed to public GitHub. The public canonical SKILL.md and owner ZIP/PDF remain unmodified.
