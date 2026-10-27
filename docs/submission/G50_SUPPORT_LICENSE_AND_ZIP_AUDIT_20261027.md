# G50 — Official UGREEN support clarification and FlowPilot licensing/package review

Date 2026-10-27 KST | Branch lead/ugreen | Private correspondence is NOT committed.

## Confirmed technical-support guidance (paraphrased, not the private email)
1. UGREEN technical support reported no separate applicable license for official Uliya Skill Kit v0.7.3 and indicated entrants may choose MIT, Apache-2.0, or BSD for their own work. This does NOT amend official Hackathon rules, prove title to vendor assets, or grant permission to redistribute vendor kit source.
2. When a submitted package contains no third-party components or redistributed code, the declaration may accurately say None / no third-party components redistributed. This is a statement about actual ZIP contents, not the development tools used.
3. AI-assisted development was confirmed acceptable for the method described in the entrant's inquiry, conditioned on explicit disclosure of AI use and nonredistribution of the official toolkit code. This response is not an eligibility award, rights warranty, official Creator execution or successful submission.
No sender address, personal identities, email headers, identifiers, attachments or original email body stored here.

## MIT recommendation — entrant-owned elements only
RECOMMENDED / NOT YET APPLIED: MIT for the entrant-authored FlowPilot Skill instruction text. Require owner approval and an appropriately identified copyright holder before applying an actual LICENSE or distributing as licensed. MIT must NOT purport to relicense UGREEN's official Skill Kit, registered experts, documentation or third-party assets. Separately applicable site/service terms and hackathon rules continue to govern the platform.
State transition: previous broad SDK-license ambiguity -> support clarification RECEIVED, package-component disclosure pathway CLEAR IF TRUE; release/IP signoff still PENDING. No further blanket-license research required unless a concrete new conflict appears.

## Actual archived G46 ZIP byte inspection (2026-10-27)
Inspected exact archived UGREEN_FlowPilot_G46_OWNER_REVIEW.zip stored in the development session. ZIP SHA256 973ec305f479ba88963e8541ebd9e34de1394ca4e5cf76f2ee102ad46c823919; exactly ONE member flowpilot-nas/SKILL.md, 7495 UTF-8 bytes, SHA256 985713d709aa36ad3e590557aac242be860716834f31eb27ff460bee960184b0. No Python, JavaScript, binary, symlink, vendor SDK tree or executables in the ZIP. This does not certify all legal originality of the Markdown's wording. Archived G46 is NOT the new G49 Skill.
Current G49 Skill SHA256 47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b. New tools/flowpilot_package_audit.py checks actual ZIP entry count/path/type, byte parity, CRC, size and source identity; tools/flowpilot_round1_preview.py now invokes that check and embeds the result in its generated manifest. The new G49 ZIP has NOT yet been independently downloaded and checked in this session; do not claim it passed before observing CI output.

## Submission PDF and AI disclosure
docs/submission/flowpilot_round1_qas_20261027.json now separates OpenAI ChatGPT GPT-6 assistance on current FlowPilot from OpenAI Codex assistance on earlier related ProjectReady work. It clearly states the new candidate was NOT generated through official Creator, and that official Uliya Kit source is not included or redistributed. G50 PDF preview generated locally: ONE A4 page, exact 10 official questions, 359 answer words (limit 500), SHA256 613df37998292cad6fa003fa35f9cf07486b675ec28c6a41818c6fa0475d74b8. Local preview not paired to a newly audited ZIP; owner approval and fresh CI package parity pending.

## Owner's development sequence and 2-hour NAS trial conditions
MVP offline plan→evidence integration and 5 synthetic cases implemented; compare to first design: NL interpretation keyword limited, dynamic plan generated, evidence/consent boundary tested, actual verified registered expert delegation 0, live data flow 0, generalized workflow engine deferred. Offline test suite 66/66 PASS on identical Git blob files in Python3.13; GitHub full suite and official checker on current G49 SHA NOT YET observed.
Follow docs/operations/NAS_FREE_TRIAL_2H_EXECUTION_RUNBOOK_20261027.md in full. Do NOT start free trial without entrant approval and Uliya/Expert Agent rights verification. On test access, first 15 minutes verify permission and stop immediately if not available; only synthetic non-sensitive folders, 2h target and backup hour conditional. No simulated NAS proof, workaround or broader NAS crawling. Continue Round1 preparation independent of free trial.

All original G36/G37, earlier G46 PDF/ZIP, and G49 Skill candidate bytes are preserved. NOT SUBMITTED to Devpost.
Rules: https://ugreenhackathon.devpost.com/rules
