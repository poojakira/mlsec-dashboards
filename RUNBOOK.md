# RUNBOOK — mlsec-dashboards

FastAPI server that serves static per-project HTML dashboards and aggregates JSON
evidence files from sibling ML-security repos into authenticated API endpoints.

> **Static, last-measured data — not live monitoring.** The per-project dashboards
> embed benchmark numbers directly in HTML. `/api/metrics` reads whatever JSON
> evidence files exist in locally-cloned sibling repos at request time; it does not
> run any tools or produce live measurements. If a sibling repo is not cloned next
> to this one, its metrics simply will not appear.

## Install

```bash
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell: venv\Scripts\Activate.ps1)
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## Start the server

`DASHBOARD_API_KEY` is **required**. Without it, `/api/*` endpoints return HTTP 500
("Server misconfigured") — this is intentional fail-closed behavior so the API is
never silently unauthenticated.

```bash
# bash
export DASHBOARD_API_KEY="your-secret-key"
python dashboard_server.py
```

```powershell
# PowerShell
$env:DASHBOARD_API_KEY = "your-secret-key"
python dashboard_server.py
```

Server listens on `http://127.0.0.1:8080`. Interactive API docs at `/docs`.

## Verify endpoints (verified outputs)

```bash
# Health — no auth required
curl http://localhost:8080/health
# {"status":"ok","service":"mlsec-dashboard-hub","version":"3.0.0"}

# Main dashboard (HTML) — HTTP 200
curl -i http://localhost:8080/

# Repo evidence discovery — requires the API key
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/status
# {"repos":{"aws-agent-identity-guard":{"exists":true,"evidence_file_count":1,...},...}}

# Aggregated metrics — requires the API key
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/metrics
# {"repos":{...},"total_repos_with_evidence":N,"ts":...}

# Wrong / missing key -> HTTP 401
curl -i http://localhost:8080/api/status
# HTTP/1.1 401 Unauthorized
```

On Windows PowerShell, `curl` is an alias for `Invoke-WebRequest`; use
`Invoke-WebRequest -Uri ... -Headers @{"X-API-Key"="your-secret-key"}` instead.

## Run the tests

```bash
pytest tests/ -q
# 25 passed
```

Covers: unauthenticated health check, API-key auth (accept/reject/missing-env→500),
`/api/status` and `/api/metrics` shape, metric extraction (flat + nested), safe JSON
parsing (valid/invalid/missing), index-serving fallbacks (missing file → fallback,
unreadable file → clean 500), and the 10 MB evidence-file size cap.

## Add new metrics

1. Add metric keys to `_extract_metrics()` in `dashboard_server.py`.
2. Drop evidence JSON into a sibling repo's `evidence/`, `results/`, `metrics/`,
   `reports/`, or `output/` directory (files ≥10 MB are skipped by design).
3. Register new sibling repos in the `SIBLING_REPOS` list.
4. Add a dashboard panel HTML file in the appropriate subdirectory.
5. Restart the server to pick up changes.

## Troubleshooting

- **`/api/*` returns 500 "misconfigured"**: `DASHBOARD_API_KEY` is not set. Set it and restart.
- **`/api/*` returns 401**: Missing or wrong `X-API-Key` header.
- **Empty metrics**: Sibling repos are not cloned next to this repo, or they contain no JSON evidence.
- **Port in use**: `uvicorn dashboard_server:app --port 8081`.
- **Import errors**: Confirm the venv is activated and `pip install -r requirements.txt` ran.
