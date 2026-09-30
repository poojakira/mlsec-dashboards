# Security Audit — mlsec-dashboards

**Audit date:** 2026-09-29  
**Scope:** FastAPI dashboard hub, static serving, evidence-file aggregation, API authentication, CORS, filesystem boundaries, rate limiting, container, and CI.

## Findings captured before this remediation pass

| ID | Severity | Finding | Status |
|---|---|---|---|
| DASH-001 | Medium | Authenticated `/api/*` requests are now bounded by a per-peer/API-key rate limiter before evidence aggregation work. | Fixed |
| DASH-002 | Medium | Production now defaults to same-origin browser access and accepts only explicitly configured, validated `DASHBOARD_ALLOWED_ORIGINS`; wildcard origins are rejected. | Fixed |
| DASH-003 | Low | Configured repository names are syntax-validated and resolved paths are confined beneath the configured evidence root before files are read. | Fixed |
| DASH-004 | Info | Individual evidence files are capped at 10 MB and JSON parse failures are handled safely. | Verified |

## Existing controls verified

- Production API key minimum length.
- Auth on `/api/status` and `/api/metrics`.
- Production evidence-root requirement.
- GET-only CORS policy.
- Safe JSON parsing and evidence-file size cap.
- Non-root container.
- Secret-hygiene CI.

## Verification plan

Add low-overhead throttling, configurable owned origins, and path confinement; then run dashboard tests and production gate.
