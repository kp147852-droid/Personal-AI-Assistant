# Security Notes

## Current Controls

- Backend listens on `127.0.0.1`.
- Non-local client requests are blocked in middleware.
- Trusted hosts limited to localhost.
- CORS restricted to local origins by default.
- Single-user mode required at startup (`SINGLE_USER_MODE=true`).
- No relay/peer service included in this build.

## Secrets Handling

- Keep secrets in `backend/.env`.
- Never commit `backend/.env` or API keys.
- Rotate keys immediately if exposed.

## Threat Model (Local Build)

- Designed for one user on one machine.
- Protects against accidental network exposure.
- Not intended as a public multi-tenant service without additional auth and network controls.

## Recommended Next Hardening

- Add optional API bearer token check for all `/api/*` routes.
- Add at-rest encryption for sensitive local memory fields.
- Add structured audit logs for admin/debug events.
- Add dependency scanning (`pip-audit`) in CI.
