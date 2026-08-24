# RUNBOOK — mlsec-dashboards

## Overview
FastAPI server serving local dev metrics dashboards.

## Install
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Start Server
```bash
export DASHBOARD_API_KEY=your-secret-key
python dashboard_server.py
```
Server runs at `http://localhost:8080`. API docs at `/docs`.

## View Dashboards
- Main dashboard: `http://localhost:8080/`
- Metrics API: `http://localhost:8080/api/metrics`
- Health check: `http://localhost:8080/health`

## Add New Metrics
1. Define new metric keys in the `_extract_metrics()` function inside `dashboard_server.py`.
2. Add evidence JSON files to a sibling repo's `evidence/`, `results/`, or `metrics/` directory.
3. Register new sibling repos in the `SIBLING_REPOS` list in `dashboard_server.py`.
4. Add dashboard panel HTML in the appropriate subdirectory (e.g., `ml-security-command-center/`).
5. Restart server to pick up changes.

## Troubleshooting
- **Port in use**: Kill existing process or use `uvicorn dashboard_server:app --port 8081`.
- **Import errors**: Confirm venv is activated and deps installed.
- **Stale metrics**: Check that sibling repo evidence files are up to date.
- **API returns 500**: Ensure `DASHBOARD_API_KEY` environment variable is set.
