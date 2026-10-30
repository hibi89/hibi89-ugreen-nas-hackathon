# Two distinct UGREEN artifact lanes (2026-10-30)

**Local FlowPilot development pilot**: the distributable ZIP built by
`tools/build_flowpilot_pilot_zip.py` contains Python and Windows launchers,
requires actual four-capability offline acceptance, and explicitly marks
`eligible_for_official_ugreen_submission: false`. It is for development,
end-user pilot testing, and standalone local evidence only.

**Official Devpost submission**: governed by `skill/flowpilot-nas/SKILL.md`,
the original source hash, existing `tools/flowpilot_package_audit.py`,
Round 1 PDF/Skill ZIP builder and the official Uliya Creator review. Official
UGREEN rules prohibit Python executable/script source and extra manifest
files inside Skill submission ZIPs. Neither lane may represent itself as
validated NAS/Uliya until actual official vendor runtime verification.

CI now explicitly builds the local pilot ZIP and proves the already existing
official Skill archive auditor REJECTS it. This does not initiate a Devpost
submission, install a third-party kit or alter G52/lead release artifacts.
