# Doctor exit code now represents preview eligibility — 2026-10-30

`flowpilot_source_doctor.py` reports separate fields for HAE+SOVIA preview
readiness and full HAE+SOVIA+DBVORA execution readiness. Its CLI exit code
now indicates only whether the **non-writing preview** can start.
Exit code 0 with `owner_local_synthetic_execution_readiness: false`
must never be interpreted as authorization for DBVORA execution.
The browser's approved execution path independently rechecks all three
source checkouts. No NAS, Uliya or customer-data reads are implied.
