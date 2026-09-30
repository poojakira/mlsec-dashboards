# Security Audit — mlsec-dashboards

**Audit date:** 2026-09-29  
**Scope:** FastAPI dashboard hub, static serving, evidence-file aggregation, API authentication, CORS, filesystem boundaries, rate limiting, container, and CI.

## Findings captured before this remediation pass

| ID | Severity | Finding | Status |
|---|---|---|---|
| DASH-001 | Medium | Authenticated evidence aggregation endpoints have no request-rate limiter despite potentially reading many JSON evidence files per request. | Open |
| DASH-002 | Medium | Production CORS is hardcoded to localhost rather than an explicit owned-domain configuration. | Open |
| DASH-003 | Low | Repository names from operator configuration are joined under the evidence root without explicit path-confinement validation. | Open |
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
