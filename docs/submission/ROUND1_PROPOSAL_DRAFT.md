# ProjectReady NAS — UGREEN Round 1 Proposal

> **DRAFT / NOT SUBMITTED — 2026-10-24 KST**. Ten substantive answers total **351/500 English words**. Do not imply official NAS, validator, privacy or licensing approval.

## 1. One sentence: What does the Skill do?

ProjectReady NAS checks an owner-selected project delivery folder for missing required files, ambiguous version candidates, and unresolved verification gaps, then reports a read-only readiness verdict.

## 2. Who is the target user and problem?

Freelancers, small teams, and creators frequently hand off NAS-hosted projects with scattered revisions, incomplete deliverables, and unclear approval status. Manual review is repetitive and errors can delay delivery.

## 3. What is your proposed solution?

An evidence-first checklist review that distinguishes PRESENT, MISSING, and NOT_CHECKED, flags version conflicts for human approval, and refuses to label a delivery READY when evidence or permissions are insufficient.

## 4. What is the Core User Flow?

The owner chooses one authorized folder and specifies mandatory deliverables. The Skill checks permitted file listings, identifies possible missing items and competing versions, optionally reviews individually approved documents, and returns a traceable READY, BLOCKED, or NEEDS_REVIEW report.

## 5. What substantive difference does your idea offer compared with existing tools or conventional AI solutions?

Unlike generic chat summaries or filename-based cleanup utilities, the workflow treats incomplete scans as uncertainty rather than absence, avoids guessing the final version, and requires explicit evidence before declaring a project ready.

## 6. Which UGREEN AI NAS capabilities will be used, and at which step in the workflow?

Planned file-agent ug-filesystem ls, find, and stat actions support owner-scoped discovery; separately authorized document-agent metadata, qa, or extract actions may support document inspection. These names are verified in the public catalog, not on a live NAS.

## 7. What was your technical approach? Describe the planned Skill workflow, supported NAS CLI capabilities, expert agent orchestration, required inputs, permissions, AI model choices, and data handling, as applicable;

A Markdown Uliya Skill coordinates a folder-scoped file review, an optional explicitly approved document check, deterministic evidence classification, and a fail-closed verdict. Inputs are the folder, checklist, and review consent. Runtime Agent registration, effective permissions, invocation syntax, and model data flow require official verification; no external service is deliberately configured.

## 8. What is the current development status? Identify what was implemented already, not yet implemented, or is pending NAS validation if selected to be a Finalist.

An original Skill draft, linked Markdown references, offline missing-file and version-review logic, policy safeguards, combined reporting, synthetic test scenarios, and package preflight are implemented. No official Uliya validator, installed-Agent call, NAS execution, or real privacy audit has been completed.

## 9. What is your final validation plan? Name two core test cases and one edge case to validate if selected as a Finalist.

Core case 1: all required files present with complete authorized listing and attributable evidence. Core case 2: one genuinely missing required file and two ambiguous final-version candidates. Edge case: access denied or truncated listing must yield NOT_CHECKED, never a false READY.

## 10. Are there any known limitations of your Project? Describe current known limitations, technical risks, and any external dependencies.

Official runtime support, Agent permissions, result completeness, content processing location, and SDK licensing remain unverified. A name match cannot prove version authority or confidentiality. The Skill never mutates files; uncertain results require human review.

## Third-party and AI declarations (separate from 10 answers)

- **ai assistance:** OpenAI ChatGPT assisted drafting, skill design, offline prototype code, unit tests and review; human entrant controls the project and submission.
- **platform:** UGREEN Uliya/UGOS public official Starter Kit and file/document expert agent catalog (referenced, not bundled); official SDK license and runtime not verified.
- **other libraries:** No external executable library or proprietary SDK files included inside proposed Markdown Skill ZIP. Offline prototyping uses Python standard library; no Python runtime included in Skill.
- **data flow:** No customer NAS data has been accessed. Future owner-scoped NAS reading requires installed Agent, permission, and local/cloud processing verification.

**Official prompt source:** https://ugreenhackathon.devpost.com/rules
**Production decision:** Submission requires participant review, verified external rights, approved PDF and final ZIP; neither official NAS validation nor Devpost submission has occurred.

