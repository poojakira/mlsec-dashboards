# Security Audit — mlsec-dashboards

**Original Audit Date:** 2026-08-06  
**Remediation Date:** 2026-08-07  
**Current Status:** Server-side critical/high findings remediated in v3.0.0; legacy static UI live-mode references are not production-supported.

---

## Remediation Summary

| Finding | Severity | Status | Fix |
|---------|----------|--------|-----|
| CRITICAL-1: Subprocess execution | Critical | ✅ Fixed | All subprocess/asyncio.create_subprocess_exec calls removed. Server reads static files only. |
| CRITICAL-2: No authentication | Critical | ✅ Fixed | Token-based auth via X-API-Key header (env var DASHBOARD_API_KEY). |
| HIGH-1: CORS wildcard | High | ✅ Fixed | CORS restricted to localhost origins only. |
| HIGH-2: Tokens in query strings | High | ✅ Fixed in tracked HF page/server docs | Auth uses header-based API key only; browser-supplied HF token query flow removed from the tracked HF scanner page. |
| M-01: No dependabot.yml | Medium | ✅ Already present | .github/dependabot.yml exists. |
| M-02: No rate limiting | Medium | ⚠️ Open | Recommend adding slowapi or similar for production. |
| M-03: No request size limits | Medium | ✅ Mitigated | Server only serves static files and reads local JSON. No request body parsing on API endpoints. |

---

## Architecture Changes (v2.0 → v3.0)

### Removed
- All `asyncio.create_subprocess_exec()` calls
- All `subprocess` module usage
- Server-side SSE endpoints that executed CLI tools (`/sse/hf-scan`, `/sse/llm-eval`, `/sse/adv-eval`, `/sse/poison-eval`)
- Unauthenticated proxy to external MCP gateway
- `httpx` dependency (no outbound network calls)
- Wildcard CORS (`allow_origins=["*"]`)
- Query-string token parameters

### Added
- `X-API-Key` header authentication from `DASHBOARD_API_KEY` env var
- Localhost-only CORS configuration
- `/api/status` — reads local evidence files (no network, no subprocess)
- `/api/metrics` — aggregates metrics from evidence JSON files
- Static file serving via FastAPI `StaticFiles` mount
- Proper error handling with structured HTTP responses

---

## Remaining Recommendations

1. **Rate limiting** — Add `slowapi` if exposed beyond localhost.
3. **HTTPS** — Use a reverse proxy (nginx/caddy) with TLS for non-local deployments.
4. **API key rotation** — Implement key rotation policy if deployed long-term.
5. **Audit logging** — Add request logging middleware for access tracking.
