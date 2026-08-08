# ML Security Dashboard Hub

Unified dashboard for all ML security portfolio tool metrics. Serves static project dashboards and aggregates evidence data from sibling repositories via a secure API.

## Install

```bash
pip install fastapi uvicorn
```

## Usage

```bash
# Set your API key (required for /api/* endpoints)
export DASHBOARD_API_KEY=your-secret-key

# Start the server
uvicorn dashboard_server:app --port 8080
```

Then open http://localhost:8080 in your browser.

## API Endpoints

All `/api/*` endpoints require an `X-API-Key` header matching `DASHBOARD_API_KEY`.

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /` | No | Main dashboard HTML |
| `GET /health` | No | Health check |
| `GET /api/status` | Yes | Which sibling repos exist and have evidence files |
| `GET /api/metrics` | Yes | Aggregated test counts, FP rates, detection rates |

### Example

```bash
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/metrics
```

## Features

- **Token authentication** — API key via `X-API-Key` header from environment variable
- **CORS restricted to localhost** — No wildcard origins
- **Real metrics aggregation** — Reads evidence JSON from sibling repos
- **Static dashboard serving** — Each project's dashboard served at `/<project-name>/`
- **No subprocess execution** — All RCE vectors from the previous version removed
- **Proper error handling** — Structured error responses with appropriate HTTP status codes

## Static Dashboards

Each project has its own dashboard served as static HTML:

- `/aws-agent-identity-guard/`
- `/hf-model-provenance-scanner/`
- `/mcp-security-gateway-monitor/`
- `/llm-redteam-framework/`
- `/adversarial-ml-lab/`
- `/dataset-poisoning-detector/`
- `/PulseNet-RUL-Forecasting/`
- `/attack-v19-core/`

## Security

See `SECURITY_AUDIT.md` for audit history. All critical and high findings from the v2.0 audit have been remediated in v3.0.
