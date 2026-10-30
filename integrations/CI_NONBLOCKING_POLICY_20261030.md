# UGREEN isolated integration CI non-blocking policy — 2026-10-30

Previous workflow cancelled a currently executing job whenever new feature code was pushed.
This repeatedly left a long chain of unverified commits, despite successful older CI.
The updated workflow keeps active jobs running instead of cancelling them; queued jobs
are managed by GitHub concurrency, and only committed source/test/evidence changes
trigger these checks. Documentation-only integration runbooks do not start checks.

Development remains nonblocking: no code step waits for an Actions conclusion.
Report passing test counts only when the exact source SHA job completes.
Do not treat a cancelled queued job as a test failure, or a prior SHA success as a new PASS.
Public CI runs fake private HAE/DBVORA sources; NAS and Uliya remain NOT_RUN.
