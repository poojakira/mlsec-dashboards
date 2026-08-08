# ML Security Dashboard Hub

Unified dashboard server for the ML Security Engineering portfolio. Serves interactive dashboards for all portfolio tools and aggregates real metrics from sibling repository evidence files via authenticated API endpoints.

## Install

```powershell
git clone https://github.com/poojakira/mlsec-dashboards.git
cd mlsec-dashboards
py -m pip install fastapi uvicorn
```

## Run

```powershell
$env:DASHBOARD_API_KEY = "your-api-key-here-min-16-chars"
py -m uvicorn dashboard_server:app --port 8080
# Open http://localhost:8080
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | Main dashboard HTML |
| GET | `/health` | No | Health check for load balancers |
| GET | `/api/status` | Yes | Repo evidence availability status |
| GET | `/api/metrics` | Yes | Aggregated metrics from all portfolio tools |

All authenticated endpoints require the `X-API-Key` header.

## Verify

```powershell
curl http://localhost:8080/api/status -H "X-API-Key: your-key"
```

Expected response: JSON with repo availability and evidence file counts.

## Architecture

The server reads JSON evidence files from sibling repository directories (e.g., `../aws-agent-identity-guard/evidence/`). No subprocess execution — all data is read from committed artifacts.
