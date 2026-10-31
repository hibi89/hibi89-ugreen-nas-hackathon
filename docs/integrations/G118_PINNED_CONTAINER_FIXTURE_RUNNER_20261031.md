# G118 fixed container-internal fixture workflow runner (2026-10-31 KST)

## Scope
Built \`tools/flowpilot_container_fixture.py\` as the next layer after G117 safety-gated Docker smoke contract. Unlike the G117 environment-only marker, G118 has two **genuine fixed Python fixture scripts** designed to run inside a restricted container: (1) synthetic CSV Decimal aggregation with invalid-numeric rejection and exact output test, (2) synthetic local file presence/missing-and-repaired test. Both scripts run with the host Python interpreter in CI as a first correctness gate. This does NOT prove that Docker ran on the CI host.

## Execution gate
Default \`python tools/flowpilot_container_fixture.py --goal "필수 파일 확인해줘" --image "python@sha256:<TRUSTED_64_HEX_DIGEST>"\` gives the plan, never executes Docker. Only a separately authorized local invocation with \`--approve-local-docker-fixture\`, a real locally available pinned Python image, verified local Unix Docker socket and fresh local CLI config may attempt a container run. CLI enforces Docker no-pull, no-network, read-only root, non-root, no mounts, cap-drop, resource and time limits. No NAS paths, user files, credentials, arbitrary source or remote Docker contexts are passed into the container.

Only exact G115 supported goals resolve to the two fixed templates. Unsupported requests are blocked. A synthetic result receipt must match an exact known schema to pass. A mocked Docker subprocess regression only proves the flags/receipt parser; real container execution and host isolation remain NOT_RUN/UNVERIFIED in ChatGPT runtime without a trusted Docker socket.

## Future acceptance
An authorized native local Docker environment must separately prove exact-image availability/provenance, actual command running under no-network restrictions and result readback. This is distinct from NAS Skill's registered Expert contract; no direct NAS Docker operation has been proven or authorized. Never state "safely installed on NAS" based on G118. Official G103 Checker, entrant rights and submission remain HOLD.

## Tests
\`python -m unittest discover -s tests -p 'test_flowpilot_container_fixture.py' -v\`. Exact Linux/Windows repository CI SHA is required for verified completion. Original \`SKILL.md\`, private G103 owner ZIP/PDF, third-party components and master ledger untouched.
