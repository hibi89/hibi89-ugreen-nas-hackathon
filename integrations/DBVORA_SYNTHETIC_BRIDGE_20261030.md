# UGREEN synthetic DBVORA bridge — 2026-10-30

The official competition SKILL.md, PDF and ZIP are unchanged.

Two designs were compared: (A) vendoring or importing private DBVORA into public UGREEN (rejected: private-source leakage / CI access / licensing) and (B) a narrowly injected metadata-only callable on a **new disposable LA-generated SQLite ledger** (selected: zero private code copied and no user-data access).

The optional `dbvora_reader` executes **only after** owner-approved local lstat and separate exact-plan SHA approval, successful synthetic LA write, and verification that the disposable ledger contains the expected synthetic rows. The unmodified standard path does not call DBVORA. Output is redacted integer schema counts and source-provenance **not claimed**; any schema/engine/provenance failure refuses and does not produce success. Public Actions uses a fake P0-contract reader and synthetic SQLite; it does **not** invoke the actual private DBVORA code. To establish private-source integration later, run only from a trusted pinned private DBVORA checkout with legitimate permissions, use synthetic fixture only, and record exact SHA / tests. Never import or publish private DBVORA source in public UGREEN.

Current evidence: feature branch tests and CI must be checked for their exact SHA. This alone does not prove actual private DBVORA, NAS, official Uliya Agent, or submission; all external/release gates remain HOLD.
