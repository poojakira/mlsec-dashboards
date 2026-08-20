# mlsec-dashboards

FastAPI server that serves per-repo metrics dashboards for the ML security portfolio. API-key authenticated, CORS-enabled, with a shared design system across 12 dashboard pages.

## What It Does

- Serves static HTML dashboards for each portfolio repo (test counts, rule counts, status)
- Aggregates evidence files (results, metrics, reports) from sibling repos
- Exposes REST endpoints for programmatic metrics access
- Shared CSS/JS design system for consistent styling

## Dashboards Served

```
/                                    Main portfolio overview
/aws-agent-identity-guard/           IAM rule scanner metrics
/hf-model-provenance-scanner/        Model provenance dashboard
/mcp-agent-security-gateway/         MCP gateway metrics
/llm-redteam-framework/              Red team framework status
/adversarial-ml-lab/                  Adversarial ML metrics
/dataset-poisoning-detector/         Poisoning detector status
/model-privacy-attacks/              Privacy attack metrics
/attack-v19-core/                    ATT&CK v19 library status
/attack-detection-engine/            Detection engine dashboard
/PulseNet-RUL-Forecasting/          PulseNet metrics
/unified-ml-security-platform/       Platform integration status
```

## Quick Start

```bash
pip install fastapi uvicorn

# API key required for authenticated endpoints
export DASHBOARD_API_KEY="your-key-here"
uvicorn dashboard_server:app --port 8080

# Or open index.html directly for static view (no server needed)
```

## API

```bash
# Health check
curl http://localhost:8080/health

# Aggregated metrics (requires API key)
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/api/metrics
```

## Structure

```
dashboard_server.py              FastAPI app (auth, CORS, evidence aggregation)
index.html                       Main dashboard (20 KB)
shared/
  design-system.css              Shared styles (15 KB)
  dashboard.js                   Shared JS (9 KB)
<repo-name>/index.html           Per-repo dashboard pages (12 repos)
tests/
  test_dashboard_server.py       Server tests
```

## Security

- Token-based auth via `DASHBOARD_API_KEY` env var (constant-time comparison)
- CORS middleware configured
- No subprocess execution — reads only static JSON evidence files
- Internal development tool, not production-facing

## Dependencies

```
fastapi
uvicorn
```

## License

MIT
