# G252 — Owner decision + version evidence readback (LOCAL ONLY)

No external provider, NAS access, source content read, owner file write, or auto-repair. Completes the critical evidence-integrity gap after G251 by inspecting two existing local privacy-redacted JSON files only with explicit opt-in.

Alternative A: silently re-read original owner/NAS source files or store proof on a server — rejected for privacy, API cost and unsupported NAS permissions.
Alternative B (implemented): bounded read-only G249/G251 receipt verification against an original G251 SHA-256 kept separately from the decision file. Detects changed scope/evidence bytes, altered manual choice (including another allowed code), extra private fields, duplicate JSON keys and symlinked files; returns non-sensitive codes. Neither an owner's authority nor vendor provenance can be authenticated by a plain hash.

Run from repo root using trusted disposable local reports:

```bash
python tools/flowpilot_g252_decision_readback.py --evidence /ABSOLUTE/evidence.json --decision /ABSOLUTE/owner-decision.json
python tools/flowpilot_g252_decision_readback.py --evidence /ABSOLUTE/evidence.json --decision /ABSOLUTE/owner-decision.json --approve-local-read --expected-decision-sha256 <ORIGINAL_G251_OUTPUT_DIGEST>
```

The first command MUST return WAITING_EXPLICIT_LOCAL_READ_APPROVAL without reading inputs. The second explicitly permits two read-only local JSON files and verifies the exact G251 creation receipt hash. The original G251 digest must come from a separate, independently retained output, not from the decision file being verified. Any invalid schema, unsupported multiple-candidate format, missing receipt SHA or mismatch fails closed with exit status 2. No write or retry; a hash is NOT a digital signature. Stable symlink/reparse point checks are non-atomic on adversarial mutable filesystems, especially on Windows. Never use this as evidence of actual NAS rights or registered Uliya Expert actions.

Local focused validation: 29 PASS, 0 FAIL, 0 SKIP (G251 13 + G252 16); end-to-end process CLI verified, mismatch exits 2. GitHub cross-platform CI is separately required before whole-product score credit. Release gate HOLD.
