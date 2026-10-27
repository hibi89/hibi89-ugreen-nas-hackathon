# G62 — Consented read-only local-folder metadata pilot

Decision: build working product capability rather than only more synthetic reports. The new command reads metadata of **actual, owner-chosen local file paths** after explicit, per-invocation consent, and reports bounded status with no filenames, root paths or contents in JSON. It does not access this GitHub operator's NAS, Uliya, any SaaS connector, documents, or customers' data. It is **development-only Python, not part of the UGREEN Markdown Skill submission ZIP**.

## Usage (owner runs only if desired)
```powershell
python tools/flowpilot_owner_local_audit.py --root "C:\path\to\a\synthetic-test-folder" --required "README.md" --required "release/output.pdf" --approve-local-metadata
python tools/flowpilot_owner_local_audit.py --root "C:\path\to\a\synthetic-test-folder" --required "release/final.pdf" --candidate "release/final.pdf=release/final_v2.pdf" --goal "compare versions" --approve-local-metadata
```
Without `--approve-local-metadata`, the CLI returns `WAITING_APPROVAL` and never touches the folder. Before metadata access, validate every relative path and version mapping, refuse write/transfer intent, then inspect only specific names (never recursive walk, no file contents, no hashes, no network or processes). Reports only index + local observation state + local reference count and always `nas_verified:false`, `registered_uliya_agent_invoked:false`, `release_gate:HOLD`. A missing file is `MISSING` only when exact relative parent checks complete. A symlink/junction/unsupported file is `NOT_CHECKED`; access failures conservatively invalidate completeness.

### Limitations
This script does not establish local-only processing for any future actual Uliya delegation, nor that a folder is non-NAS if it is mounted as a local drive. Windows path-based `lstat` checks are not atomic against rapid concurrent replacement of intermediate folders; **use only a trusted, stable, disposable local test folder**, not other users' untrusted changing trees. UNC paths explicitly disallowed and reparse/junctions rejected; no root or raw path ever echoed. This pilot does not prove official Creator provenance or contest execution.

### Readiness
17 new regressions check 2 present/missing/version states, consent-before-access, mutation rejection, actual OS symlink traversal, local byte preservation, invalid roots/paths, named candidate validation, bounded result and CLI shell output. G62 full repository tests expected **463**, awaiting exact-source GitHub CI. Canonical contest Skill SHA256 remains `47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b`, owner-review G52 PDF/ZIP unchanged; rights/Creator/NAS/Devpost HOLD. General 3h NAS demo target Nov 3–5 KST conditional; any earlier trial requires permissions and owner approval.
