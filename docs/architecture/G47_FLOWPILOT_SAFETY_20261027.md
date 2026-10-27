# G47 FlowPilot — read-only security hardening / no NAS execution
Date 2026-10-27 KST. Scope: off-ZIP pure-Python planner/evidence and GitHub CI only.

## Confirmed safety gap and correction
Pre-G47 Korean `_WRITES` regular expression used word boundary markers around Hangul stems. A conjugated mutation such as '파일 확인 후 삭제해줘' could bypass the write guard and enter read-only planning. New policy explicitly checks Korean stems without English word-boundaries; English copy/share/publish/export/erase are also blocked. This does not claim generalized multilingual natural language security, just tested cases.
Pre-G47 path policy did not explicitly block multiple credentials aliases, .aws/.kube/.npmrc/.netrc, URL-encoded traversal markers, colon-based alternate streams or invisible Unicode format characters. Matching privacy list tightened in both planner and evidence offline modules. No real symlink resolution, runtime provenance or network protection is claimed.

## Tests and evidence
- Original G43 18 planner tests and G44 16 evidence tests remain in repo.
- G47 new tests/test_flowpilot_g47_security.py adds 8 additional privacy/write guard scenarios; official checker workflow and PDF ZIP preview workflow now require >=42 discovered tests, ALL passing, before continuing.
- Local Python 3.13 ran independently copied exact original evidence engine plus G47 restrictions: 22/22 unit tests PASS. Separately ran Korean/English mutation regex smoke: 9/9 cases PASS.
- GitHub's actual CI result for G46/G47, official checker JSON, runtime expert registration and Creator provenance were NOT available from connected tools. This is not proof of 42/42 or first-party static-pass.

## Distinct submission boundary
Do not change G46 original exact source Skill ZIP SHA256 973ec305f479ba88963e8541ebd9e34de1394ca4e5cf76f2ee102ad46c823919, PDF SHA256 f7225b229b3ce35999eb384f5c3857eaa22e8c49851bda51047330d1de7c8b1b, or original G36/G37. G47 changes off-ZIP safety prototype only; it does NOT fix the Uliya Skill runtime, where identical policies remain instructions and must be tested on official NAS if finalist.
Official Creator for newly authored FlowPilot remains NOT_RUN. First-party checker must run on exact Skill SHA 985713d709aa36ad3e590557aac242be860716834f31eb27ff460bee960184b0 before considering it validated.

## Next gate
Acquire G47 GitHub Actions diagnostics and exact checker receipt; if passing, evaluate Skill creation-tool provenance, supported delegate syntax and rights/entrant approval. No automatic Devpost upload.
