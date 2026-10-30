# Owner-selectable real local folder read-only checklist — 2026-10-30

The loopback UI now has a **real operator-selected LOCAL folder** inspection
path in addition to the five-scenario generated-fixture demo and the optional
private-source LA suite. A user types an absolute non-UNC local directory,
an allowed 1–3-intent goal, 1–30 exact relative required filenames, and
optional required=candidate version mappings. The UI explicitly asks the
owner to confirm this is a trusted **local folder, not NAS or mapped network
drive**. Browser preview returns a bounded plan/ticket **without inspecting
the folder**; a second separate checkbox and one-shot token authorize
read-only lstat metadata access for that exact validated request.

The existing FlowPilot goal parser and the existing OS lstat owner metadata
inspector are the actual engine. Results contain only step/count/review
states and negative vendor flags; no raw folder path, filenames or file
contents are emitted. Unrecognized or mutating goals, traversal, restricted
filenames, symlinks, UNC/device-root and missing consent fail closed.
This does not verify mounted NAS detection for all Windows drive letters or
defeat local filesystem race attacks; the operator must choose a trusted
non-network local directory. No HAE, SOVIA, DBVORA or NAS source is invoked
from this new route. External vendor execution and official submission remain
HOLD.

Tests: 8 workbench tests with true temp-folder lstat + 1 real localhost
HTTP request sequence; public CI exercises actual OS file metadata reads
on generated test directories, never owner data.
