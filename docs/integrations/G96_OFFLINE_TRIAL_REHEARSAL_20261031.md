# G96 — pinned public catalog → operator-normalized review (offline only)

G96 integrates G95 public SHA-pinned Uliya catalog and owner-scope consent preflight, G87 synthetic/operator-normalized read-only receipt validation, and G88 redacted owner review. No native SDK response shape or registered Expert permission is invented.

Input schema `flowpilot-trial-rehearsal-v1` has `request` (G95) and `normalized_receipts` (G87). First receipt action must match owner-selected read operation. All root, checklist, goal and consent fields must agree. Version candidate expansion is refused. Denied consent and mutation intent are stopped before evaluating receipt claims.

Run `python tools/flowpilot_uliya_trial_rehearsal.py --official-url PINNED_PUBLIC_KIT_URL --input PRIVATE_LOCAL_SYNTHETIC_JSON`. Do not commit owner/private receipts. Only public kit is retrieved; no owner data is uploaded.

Review states:
- `REVIEW_PREPARED_UNVERIFIED`: self-attested consistent, review needed.
- `OFFLINE_CONFLICT_HOLD`: contrary claims, all items NOT_CHECKED.
- `OFFLINE_INCOMPLETE_HOLD`: no complete enumeration.
- `OFFLINE_BLOCKED_HOLD`: read-only review finds a claimed missing mandatory item.
- `WAITING_APPROVAL` / `BLOCKED`: owner scope/consent or mutating intent not authorized.

All outputs omit owner paths and references; `decision=HOLD`, `release_gate=HOLD`, runtime/Creator/NAS verification flags false, and no execution payload generated. This is development tooling only, excluded from official Markdown-only contest Skill ZIP. Canonical Skill, original PDF/ZIP and master data remain unchanged.

Validation is required on the exact GitHub source SHA in Linux and Windows CI. Real registered Uliya Expert, effective permissions, native result schema, official Creator proof and Devpost submission are distinct external gates needing explicit owner authorization.
