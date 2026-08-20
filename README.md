# mlsec-dashboards

FastAPI server that serves static HTML dashboards and aggregated metrics for the ML security portfolio repos. Each sub-directory contains a standalone HTML dashboard for one repo.

## What It Does

- `dashboard_server.py` — FastAPI app with API-key auth that serves metrics endpoints
- Per-repo HTML dashboards showing test counts, rule counts, and status
- Shared CSS/JS design system for consistent styling

## What It Is Not

This is not a production monitoring system. It's a local dev tool for viewing portfolio metrics in a browser.

## Usage

```bash
pip install fastapi uvicorn
DASHBOARD_API_KEY="your-key-here" python -m uvicorn dashboard_server:app --port 8080
```

Or just open `index.html` directly in a browser for the static view.

## Structure

```
dashboard_server.py              - FastAPI server
index.html                       - Main dashboard page
shared/                          - CSS and JS shared across dashboards
<repo-name>/index.html           - Per-repo dashboard pages
tests/                           - Server tests
```

## Status

Works locally. Dashboards render committed JSON data — no live data collection.
