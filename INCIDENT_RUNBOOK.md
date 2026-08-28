# Incident Runbook — mlsec-dashboards

## What this is

`mlsec-dashboards` is a **single-file local FastAPI dev tool** (`dashboard_server.py`)
that serves static HTML dashboards and aggregates metrics from JSON evidence files in
sibling repositories. It has:

- **No database, no message queue, no Kubernetes, no load balancer, no Flask** — it is a
  plain FastAPI app run with `uvicorn` on `127.0.0.1:8080`.
- **API-key auth** on the JSON API endpoints via the `X-API-Key` header, compared against
  the `DASHBOARD_API_KEY` environment variable.
- **CORS restricted to localhost** (ports 8080 and 3000 on `localhost`/`127.0.0.1`).

### Endpoints
| Path | Auth | Purpose |
|------|------|---------|
| `GET /health` | none | Health check (`{"status": "ok", ...}`) |
| `GET /` | none | Serves `index.html` |
| `GET /api/status` | `X-API-Key` | Which sibling repos exist and have evidence files |
| `GET /api/metrics` | `X-API-Key` | Aggregated metrics from sibling-repo JSON evidence |
| `GET /<repo>/...` | none | Static files mounted per sibling-repo dashboard dir |

### Start / stop
```bash
export DASHBOARD_API_KEY=your-secret-key
uvicorn dashboard_server:app --host 127.0.0.1 --port 8080
# or: python dashboard_server.py
# Stop with Ctrl+C.
```

---

## Table of Contents
1. [Server Won't Start](#1-server-wont-start)
2. [401 Unauthorized on /api Endpoints](#2-401-unauthorized-on-api-endpoints)
3. [Stale or Empty Metrics](#3-stale-or-empty-metrics)
4. [Static Asset / Dashboard 404](#4-static-asset--dashboard-404)
5. [CORS Errors in the Browser](#5-cors-errors-in-the-browser)

---

## 1. Server Won't Start

### Symptoms
- `uvicorn` exits immediately or errors on launch.
- Browser cannot connect to `http://localhost:8080`.

### Likely causes and fixes

**Port already in use** (`[Errno 48] Address already in use` / `10048` on Windows):
```bash
# Find and stop whatever is holding port 8080
# Linux/macOS:
lsof -i :8080
# Windows (PowerShell):
Get-NetTCPConnection -LocalPort 8080

# Then re-run on a free port if needed:
uvicorn dashboard_server:app --host 127.0.0.1 --port 8090
```

**`DASHBOARD_API_KEY` not set:** the server still starts, but every `/api/*` call returns
HTTP 500 (`Server misconfigured: DASHBOARD_API_KEY environment variable not set.`). On
startup with no key set, it prints a `WARNING: DASHBOARD_API_KEY not set` banner. Fix:
```bash
export DASHBOARD_API_KEY=your-secret-key        # Windows: $env:DASHBOARD_API_KEY="..."
uvicorn dashboard_server:app --host 127.0.0.1 --port 8080
```

**Missing dependencies** (`ModuleNotFoundError: fastapi` / `uvicorn`):
```bash
pip install fastapi uvicorn
```

### Verify
```bash
curl -s http://localhost:8080/health
# Expected: {"status": "ok", "service": "mlsec-dashboard-hub", "version": "3.0.0"}
```

---

## 2. 401 Unauthorized on /api Endpoints

### Symptoms
- `GET /api/status` or `GET /api/metrics` returns `401 Invalid or missing API key.`

### Cause
The `X-API-Key` request header is missing or does not match the server's
`DASHBOARD_API_KEY` (compared with `hmac.compare_digest`).

### Fix
Send the correct key:
```bash
curl -s http://localhost:8080/api/status -H "X-API-Key: your-secret-key"
```
- Confirm the value matches the `DASHBOARD_API_KEY` the server was started with.
- If you get HTTP 500 instead of 401, `DASHBOARD_API_KEY` was never set — see
  [Server Won't Start](#1-server-wont-start).
- Note `/health` and `/` require no key; only `/api/*` do.

---

## 3. Stale or Empty Metrics

### Symptoms
- `/api/metrics` returns few or no repos, or numbers look out of date.
- `total_repos_with_evidence` is 0 or lower than expected.

### Cause
Metrics are read live from JSON files in **sibling repositories** located in the parent
directory of this repo (`../<repo-name>/`). The server scans `evidence/`, `results/`,
`metrics/`, `reports/`, `output/`, and root-level `*.json` files. If a sibling repo is
missing, or its evidence JSON has not been regenerated, results are empty or stale.

### Diagnosis
```bash
# See which sibling repos the server can find and how many evidence files each has
curl -s http://localhost:8080/api/status -H "X-API-Key: your-secret-key"
```

### Fix
- Ensure the expected sibling repos are checked out next to this one (same parent dir).
- Regenerate the evidence/metrics JSON in the relevant sibling repo (run its own
  tests/benchmark that produce the JSON files).
- Confirm the JSON is valid — malformed files are skipped silently. Files over 10 MB are
  ignored by design.
- Re-request `/api/metrics`; the data is read fresh on each request (no caching), so no
  restart is required.

---

## 4. Static Asset / Dashboard 404

### Symptoms
- `GET /` shows "No index.html found."
- A per-repo dashboard path like `/mcp-agent-security-gateway/` returns 404.

### Cause
- `index.html` is missing from the repo root (the server falls back to a placeholder page).
- A sibling-repo dashboard directory does not exist locally. Static mounts are only added
  for directories that exist under this repo's folder at startup.

### Fix
- Confirm `index.html` exists in the repo root next to `dashboard_server.py`.
- Confirm the target dashboard directory exists locally; if you add it after the server is
  already running, **restart the server** so the new static mount is registered.

---

## 5. CORS Errors in the Browser

### Symptoms
- Browser console shows a CORS policy error when a page calls the API.

### Cause
CORS is intentionally restricted to `http://localhost:8080`, `http://127.0.0.1:8080`,
`http://localhost:3000`, and `http://127.0.0.1:3000`, and only allows the `GET` method
and `Authorization` / `X-API-Key` headers. Requests from any other origin are blocked.

### Fix
- Load the dashboard from one of the allowed localhost origins (this is a local dev tool,
  not a public service).
- If you genuinely need another local origin, add it to the `allow_origins` list in
  `dashboard_server.py` and restart the server.

---

## Notes

- This is a local development/inspection tool. There is no production deployment, no
  autoscaling, no TLS termination, and no external datastore to manage. "Incident
  response" here means restarting the local process and fixing local configuration or
  sibling-repo evidence files.
