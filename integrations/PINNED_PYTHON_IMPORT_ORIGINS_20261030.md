# Import provenance hardening — 2026-10-30

The optional private-source four-stack verifier previously pinned clean Git
checkouts before `from lightning_azent import LAExecutor` and
`from sovia_la_plan_preflight import assess`. However, Python's existing
`sys.modules` cache can return code from another checkout despite the
source SHA checks, especially inside the long-lived loopback operator UI.

Both `tools.verify_private_hae_chain.run` and
`tools.verify_local_metadata_la_chain.verify` now compare the actual
`LAExecutor.preflight` and `assess` function code origins to the
expected files inside the separately SHA-pinned, clean Git checkouts.
Unresolvable, absent, symlinked, mismatching, and unverifiable code origins
fail closed without printing any private source path.

Five synthetic unit tests exercise correct, swapped, missing and
unverifiable origins; they DO NOT import private sources or claim NAS
execution. DBVORA already uses a corresponding provenance check.
These guards are not cryptographic attestation or an atomic defense against
a malicious local filesystem. Official Uliya/NAS and release gates remain HOLD.
