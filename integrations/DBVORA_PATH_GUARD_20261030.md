# DBVORA synthetic reader local-path hardening (2026-10-30)

Exact scope: optional UGREEN feature-branch adapter for **new disposable LA SQLite only**. Before any injected DBVORA reader is called, refuse non-`business.sqlite` paths, symlinks, non-regular files and multi-linked files. Two negative regression tests cover symlink substitution and unexpected filenames. This addresses a discovered local read boundary issue; the preflight is **not atomic against concurrent replacement** and is not evidence of actual NAS permission, Windows reparse safety or user-database readiness.

Original official Skill/PDF/ZIP and external private repositories remain untouched. CI tests use synthetic local fixture and simulated P0 reader; exact new commit CI outcome must be queried before PASS claims.
