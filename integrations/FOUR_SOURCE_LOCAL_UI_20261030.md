# Loopback-only UGREEN FlowPilot local operator UI

Launch from the UGREEN feature checkout with trusted, separately pinned source repositories:

    py -3.11 tools/flowpilot_four_source_local_ui.py --hae-root ..\HAE --sovia-root ..\SOVIA_sovereign --dbvora-root ..\DBVORA --output-dir C:\temp\ugreen-proof-new

The terminal prints a 127.0.0.1 URL using an ephemeral port by default.
Step 1 checks only Git source readiness. Step 2 previews all three bounded
temporary synthetic scenarios without writes. Step 3 requires a separate
checkbox and fresh one-time approval token before disposable SQLite execution.

The local HTTP server binds loopback, requires a session token on each POST,
checks Host/Origin, does not accept browser-submitted source paths and
loads no third-party assets. An optional new output directory receives
the sanitized JSON/HTML proof matrix. No customer content or NAS/Uliya call.
All results are operator-reported synthetic and release remains HOLD.
