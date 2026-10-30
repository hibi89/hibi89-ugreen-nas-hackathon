# G86 Windows CP949 Git source gate correction — 2026-10-31 KST

## Observed owner-local failure
The user ran the G86 main-repo native backend command on Windows with a Unicode checkout path. Before private HAE/LA execution, the UGREEN wrapper's Git source verification called `git rev-parse --show-toplevel` through `subprocess.run(text=True)`. Windows Python 3.11 decoded Git's UTF-8 path bytes with its CP949 default decoder. The background pipe reader raised `UnicodeDecodeError: 'cp949' codec can't decode byte 0xed in position 40`. `proc.stdout` was then `None` and the parent raised `AttributeError` on `.strip()`. The command exited 1. This is a Windows Git output decoding error, NOT evidence of failed HAE, LA, SQLite writes, or actual NAS integration.

## Fix: source code preserved, fail-closed behavior retained
- File: `tools/run_g85_native_backend.py`
- Bug-fix code SHA `f0b3b2b78c5ac08db48671d29ff9c4905afeb84e`; dedicated Unicode path regression test SHA `664833ce0e606a6d5bb5bfaa2bc91e231ed3acd7`.
- Instead of asking Git to print a Unicode absolute checkout path, run `git rev-parse --show-prefix`, which yields empty ASCII text at repository root and nonempty prefix for subdirectories; continue rejecting unexpected subdirectory execution.
- Run Git subprocess with binary stdout (no platform-default text decoding), then decode only expected ASCII Git objects and gate values. A malformed or non-ASCII Git response raises `IntegrityRefused` rather than reporting success.
- Private HAE runner/package reviewed Git blobs, execution receipt strictness, previous G85 native proof, customer source, canonical Skill, original HAE binary and all authorization gates remain unchanged.

## Verification scope
- Local independent Git probe on a disposable repository nested under Korean-named directories confirmed ASCII `--show-prefix` output at root, nonempty nested prefix, and ASCII `hash-object` output. This probe ran outside Windows and does NOT establish Windows native PASS.
- Expanded public `tests/test_g86_native_backend_integrity.py` using a temporary Korean directory, including non-ASCII fail-closed handling.
- Latest public functional CI for SHA `664833ce...`: [41101075166](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/41101075166). At evidence record preparation the run was QUEUED; do not infer PASS until confirmed.
- Windows owner-local updated G86 genuine native command has NOT been re-run after this correction. Before correction the owner command returned exit 1; prior G85 genuine native proof PASS/exit 0 is unaffected.
- Actual Uliya Expert/NAS, production, customer data, Devpost submission remain NOT_RUN / NOT_VERIFIED.

## Owner-local next command
From an existing clean checkout, fast-forward only the `_g84_local/UGREEN` replica, then call `tools/run_g85_native_backend.py` with the existing private HAE and LA checkout paths and explicit `--execute-synthetic-only`. Expected status: `G85_UGREEN_NATIVE_BACKEND_E2E_PASS`; `private_runner_integrity=G86_REVIEWED_GIT_BLOBS_MATCH`; exit code 0. Any other outcome is NOT_VERIFIED; do not repeat writes automatically.
