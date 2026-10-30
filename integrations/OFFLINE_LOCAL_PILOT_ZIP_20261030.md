# Offline FlowPilot LOCAL pilot ZIP

The public local pilot can be delivered as a reproducible, source-only ZIP
without a Git repository checkout at the end user's machine.

On the developer Windows machine, double-click
`tools/BUILD_FLOWPILOT_PILOT.cmd`. This first runs **all four actual offline
local capability checks** on disposable data and refuses packaging on failure.
On success it creates a NEW `FlowPilot_Local_Pilot.zip` in the repo root
without overwriting an existing file. Extract the zip on a Windows PC
with Python 3.11 and double-click `tools/START_FLOWPILOT_DEMO.cmd`.

The package recursively collects local Python imports from the actual browser
and acceptance entrypoints, plus three fixed Windows launchers and pilot
quickstart. It does not include .git, caches, tests, evidence, .env,
private HAE/SOVIA/DBVORA repositories or any owner/customer data. A
`MANIFEST.json` lists every source file and SHA-256 digest. Archive file
timestamps and ordering are deterministic. The manifest and ZIP result
**explicitly disclaim** NAS/Uliya verification.

Public GitHub Actions adds a test that builds the ZIP, extracts it into
a separate directory, then runs the four-stage acceptance from a different
working directory. This is stronger than compilation-only tests, but remains
a LOCAL pilot, not official UGREEN NAS Creator submission.
