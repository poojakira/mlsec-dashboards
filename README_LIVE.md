# mlsec-dashboards — Live Setup Guide

## What makes these dashboards interactive

Each dashboard has two modes:

| Mode | When | What you see |
|------|------|-------------|
| **Offline** | dashboard_server not running | Benchmark results from evidence/ — static but real data |
| **Live** | dashboard_server running | Real tool output, streaming results, live metrics |

The bridge is `dashboard_server.py` — a small FastAPI process you run locally.

---

## Quick start (3 commands)

```bash
# 1. Install the proxy dependencies
pip install fastapi uvicorn httpx

# 2. Start the proxy (keep this terminal open)
python dashboard_server.py

# 3. Open the dashboards
# Just open index.html in your browser, or serve from the repo root:
python -m http.server 8080 --directory path/to/mlsec-dashboards
# Then visit http://localhost:8080
```

The proxy runs on **port 9001**. All dashboards automatically detect it and switch to live mode.

---

## What each dashboard does live

### MCP Security Gateway Monitor
**Requires:** `pip install -e ".[server]"` in mcp-agent-security-gateway

```bash
# Terminal 1: start the gateway
cd mcp-agent-security-gateway
pip install -e ".[server]"
mcp-gateway

# Terminal 2: start the dashboard proxy
python dashboard_server.py
```

The dashboard then:
- Polls `/v1/metrics` every 2 seconds — shows live request counts, error rate, P99 latency
- Polls `/v1/health` — connection status indicator
- Live tool call inspector: paste a JSON tool call and send it to the running gateway, see BLOCKED/ALLOWED in real time
- Circuit breaker state for `inspect_call` and `inspect_output`

---

### HF Model Provenance Scanner
**Requires:** `pip install hf-model-provenance-scanner`

```bash
python dashboard_server.py  # if not already running
```

The dashboard then:
- Type any HuggingFace model ID (e.g. `gpt2`, `mistralai/Mistral-7B-v0.1`)
- Optionally paste an HF API token for private models
- Click **Scan model** — streams real `hf-scanner` output to the browser
- Findings appear with severity badges (CRITICAL/HIGH/MEDIUM/LOW)
- Scan history tracks all scans in the session

---

### LLM Redteam Framework
**Requires:** `pip install llm-redteam-framework`

```bash
python dashboard_server.py  # if not already running
```

The dashboard then:
- Select split mode (grouped/random) and seed
- Click **Run eval** — streams real `redteam-eval` stdout to the browser
- P/R/F1 cards update from the live JSON result
- Charts rebuild with live data
- The committed F1=0.93 (curated) / 0.70 (transfer) baseline is always shown for comparison

---

### Adversarial ML Lab
**Requires:** `pip install adversarial-ml-lab`

```bash
python dashboard_server.py  # if not already running
```

Select attack type (FGSM/PGD/C&W) and click **Run eval**. Live accuracy streams back.

---

### Dataset Poisoning Detector
**Requires:** `pip install dataset-poisoning-detector`

```bash
python dashboard_server.py  # if not already running
```

Select method (spectral/influence) and click **Run eval**. Live ROC-AUC streams back.

---

## All other dashboards (model-privacy, attack-v19, detection-engine, aws-guard, unified, benchmark, command-center)

These show real benchmark data from the evidence/ directories. They don't have live eval modes because they have no CLI subprocess or server interface. They check `/api/status` on load and show a live badge if the proxy is running, but the data itself is always from committed evidence.

---

## Proxy endpoints

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/health` | GET | Proxy health check |
| `/api/status` | GET | Which tools are installed + MCP reachable |
| `/sse/mcp` | GET | Live MCP gateway metrics stream (SSE) |
| `/api/mcp/inspect` | POST | Forward tool call to running gateway |
| `/sse/hf-scan?model_id=X&token=Y` | GET | Stream hf-scanner results (SSE) |
| `/sse/llm-eval?split_mode=X&seed=Y` | GET | Stream redteam-eval results (SSE) |
| `/sse/adv-eval?attack=X` | GET | Stream adversarial eval results (SSE) |
| `/sse/poison-eval?method=X` | GET | Stream poisoning detector results (SSE) |

The proxy runs on `localhost:9001`. All browser requests go to this proxy to avoid CORS issues with the real tool servers.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Dashboard shows "Offline" | `python dashboard_server.py` is not running |
| "hf-scanner not found" | `pip install hf-model-provenance-scanner` |
| "redteam-eval not found" | `pip install llm-redteam-framework` |
| MCP shows "not reachable" | `mcp-gateway` is not running (separate step) |
| CORS error in browser console | Open dashboards via `python -m http.server`, not file:// |
| Port 9001 in use | Edit `PROXY_PORT` at top of `dashboard_server.py` and update `const PROXY` in each dashboard HTML |

---

## Architecture

```
Browser (index.html / dashboard/*.html)
    │
    │  EventSource / fetch  (localhost:9001)
    ▼
dashboard_server.py  (FastAPI, port 9001)
    │                    │                    │
    │  HTTP poll          │  subprocess        │  subprocess
    ▼                     ▼                    ▼
mcp-gateway          hf-scanner CLI      redteam-eval CLI
(port 8080)          (pip package)       (pip package)
```
