# G5 advance — two core and one edge scenario (offline validation only)
Date: 2026-10-24 KST, ahead of scheduled 11/05. Code: `tests/test_core_edge_scenarios.py`.

| Scenario | Synthetic inputs | Expected contract result | Real NAS conclusion |
|---|---|---|---|
| CORE1: all requested deliverables found | Authorized complete simulated scan sees design.pdf and contract.pdf | Both presence checks PASS; overall NEEDS_REVIEW until independent version/privacy gates are proven | NOT RUN |
| CORE2: missing mandatory contract | Simulated complete authorized scan sees only design.pdf | Contract FAIL and overall BLOCKED | NOT RUN |
| EDGE1: permission denied | Simulated denied scan with no authorized observations | Both NOT_CHECKED; overall NEEDS_REVIEW (never assert file missing) | NOT RUN |

Important: the mocked `SDK_VERIFIED` source is a *contract simulation flag*, not a real first-party validation or NAS test. Therefore CORE1 does not say READY. Official Uliya Expert Agent/CLI details, permissions and actual NAS demonstration are still unverified. These Python tests are engineering evidence and must not be copied into the submission ZIP.
