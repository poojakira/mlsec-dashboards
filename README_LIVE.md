# mlsec-dashboards — Local Server Guide

`dashboard_server.py` is a FastAPI server for static dashboards plus authenticated local evidence APIs.

It does not implement the legacy SSE subprocess proxy. Browser pages that still reference `/sse/*` are legacy UI surfaces and should be treated as static/offline until matching backend routes are restored and tested.

## Quick Start

```bash
pip install -r requirements.txt
$env:DASHBOARD_API_KEY="change-me"
python dashboard_server.py
```

Open `http://localhost:8080/`.

## Supported Endpoints

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `/health` | No | Local server health check |
| `/api/status` | `X-API-Key` | Sibling repo/evidence availability |
| `/api/metrics` | `X-API-Key` | Aggregated metrics from local JSON evidence files |
| `/<dashboard>/` | No | Static dashboard pages |

Example:

```bash
curl -H "X-API-Key: change-me" http://localhost:8080/api/status
curl -H "X-API-Key: change-me" http://localhost:8080/api/metrics
```

## Unsupported Legacy Endpoints

The tracked v3 server intentionally does not expose:

- `/sse/mcp`
- `/api/mcp/inspect`
- `/sse/hf-scan`
- `/sse/llm-eval`
- `/sse/adv-eval`
- `/sse/poison-eval`

Do not pass Hugging Face tokens, API keys, or other secrets in browser query strings. Private-model scanning must be implemented server-side with header or environment-based secret handling before it is re-enabled.

## Notes

- Keep this server bound to localhost unless a reverse proxy, TLS, rate limiting, and access logging are added.
- Static dashboards are evidence viewers, not production monitoring consoles.