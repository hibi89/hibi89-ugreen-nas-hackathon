# Localhost HTTP contract verification (2026-10-30)

Add six real TCP loopback HTTP tests for the 127.0.0.1 operator interface:
home security headers, pre-approval evidence refusal, forbidden Host/Origin/session,
bounded JSON actions, one-time approval replay refusal, and SHA-256 report
integrity plus URL traversal refusal. All private source integrations are
mocked; tests do not make external requests or contact NAS/Uliya.

X-Frame-Options: DENY and Referrer-Policy: no-referrer are applied to local
HTTP pages to reduce embedding and accidental referrer leakage.
Passing these tests does not prove public hosting, vendor execution,
or the separate official Creator/Devpost submission gates.
