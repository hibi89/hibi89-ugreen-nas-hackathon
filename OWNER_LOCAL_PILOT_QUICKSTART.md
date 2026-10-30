# FlowPilot 3.0 — Owner-local functional MVP quickstart

On Windows with Python 3.11 installed and a fresh checkout of
`feature/flowpilot-ecosystem-integration`:

- Double-click `tools/START_FLOWPILOT_DEMO.cmd`. This opens the local
  browser server (127.0.0.1 only; no external network).
- Click **Verify 4 local MVP capabilities** for real automatically generated
  test files, real OS lstat, actual generated CSV aggregation and SQLite
  audit, approved local-folder metadata and separately consented content
  aggregation. The four acceptance checks use only disposable fixtures,
  never actual owner files.
- To inspect your own trusted local folder, use the **read-only** checklist.
  This never reads file contents.
- To aggregate your own local CSV, enter a local absolute folder, 1–5
  exact CSV base names, a new output filename, group and numeric amount
  columns. Confirm metadata preview and then separately approve actual
  contents being read and the creation of a new output file.
  **This third workflow reads and writes your actual local data.**
- Only the locally approved output may be downloaded. No public file names,
  contents or paths are returned to the browser in JSON metadata results.
- A distinct optional private 4-source verification panel still requires
  pinned HAE/SOVIA/DBVORA checkouts. This is NOT yet live NAS/Uliya.

To check all four main LOCAL capabilities without opening the browser,
double-click `tools/VERIFY_FLOWPILOT_LOCAL_MVP.cmd` or use
`py -3.11 tools/flowpilot_local_acceptance.py`. The command runs temporary
fixtures only, prints count/checksum receipts and exits. A PASS is local
functionality evidence, **not** an official NAS, registered Uliya, Creator
or Devpost acceptance. Release remains HOLD.
