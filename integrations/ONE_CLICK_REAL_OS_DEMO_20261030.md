# UGREEN single-click owner-local demo without private repos — 2026-10-30

Windows: double-click `tools/START_FLOWPILOT_DEMO.cmd`. Python 3.11
with the Windows `py` launcher is required. The command starts a loopback
127.0.0.1 server and opens the default browser automatically.
No HAE/SOVIA/DBVORA source checkout is required to use the first
**Run 1–3 intent real OS demo** button. The existing private-source
four-stack mode remains separately optional and explicitly gated.

Headless cross-platform smoke: `python tools/flowpilot_four_source_local_ui.py --demo-check`.
This performs five real OS lstat checks on generated disposable folders,
prints a redacted JSON result and exits without any local HTTP server.

Starting the UI does not approve synthetic SQLite writes or contact NAS,
registered Uliya Experts, external APIs, Creator or Devpost. Close the
console window or press Ctrl+C to stop the server. Browser mode is local-only.
