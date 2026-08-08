# Runbook — ML Security Dashboards

Step-by-step guide to run the dashboard server locally.

---

## Prerequisites

- Python 3.10+ (`py --version` on Windows, `python3 --version` on Linux)
- pip (bundled with Python)
- Git

---

## Step 1: Clone and Install

**Windows (PowerShell):**
```powershell
git clone https://github.com/poojakira/mlsec-dashboards.git
cd mlsec-dashboards
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn
```

**Linux/macOS:**
```bash
git clone https://github.com/poojakira/mlsec-dashboards.git
cd mlsec-dashboards
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn
```

---

## Step 2: Set API Key Environment Variable

The server requires a `DASHBOARD_API_KEY` for authentication.

**Windows (PowerShell):**
```powershell
$env:DASHBOARD_API_KEY = "your-secret-key-here"
```

**Linux/macOS:**
```bash
export DASHBOARD_API_KEY="your-secret-key-here"
```

> **Note:** For local development, any non-empty string works. For production, use a strong random key.

---

## Step 3: Start the Server

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe -m uvicorn dashboard_server:app --port 8080
```

**Linux/macOS:**
```bash
uvicorn dashboard_server:app --port 8080
```

Expected output:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

---

## Step 4: Verify with curl

**Windows (PowerShell):**
```powershell
# Health check (no auth required)
curl http://localhost:8080/

# Authenticated API call
curl -H "X-API-Key: your-secret-key-here" http://localhost:8080/api/metrics
```

**Linux/macOS:**
```bash
# Health check
curl http://localhost:8080/

# Authenticated API call
curl -H "X-API-Key: your-secret-key-here" http://localhost:8080/api/metrics
```

Expected response for health check: HTML page or JSON status.
Expected response for metrics: JSON with aggregated portfolio metrics.

---

## Step 5: Access Dashboards in Browser

Open your browser and navigate to:

| URL | Dashboard |
|-----|-----------|
| `http://localhost:8080/` | Main hub page |
| `http://localhost:8080/aws-agent-identity-guard/` | IAM linter dashboard |
| `http://localhost:8080/hf-model-provenance-scanner/` | HF scanner dashboard |
| `http://localhost:8080/adversarial-ml-lab/` | Adversarial ML dashboard |
| `http://localhost:8080/dataset-poisoning-detector/` | Poisoning detector dashboard |
| `http://localhost:8080/llm-redteam-framework/` | LLM red team dashboard |
| `http://localhost:8080/model-privacy-attacks/` | Privacy attacks dashboard |
| `http://localhost:8080/attack-v19-core/` | ATT&CK v19 dashboard |
| `http://localhost:8080/ml-security-command-center/` | Command center dashboard |
| `http://localhost:8080/mlsec-benchmark-suite/` | Benchmark suite dashboard |
| `http://localhost:8080/mcp-security-gateway-monitor/` | MCP gateway dashboard |
| `http://localhost:8080/unified-ml-security-platform/` | Unified platform dashboard |

**Hosted version (no server needed):**
https://poojakira.github.io/mlsec-dashboards/

---

## Troubleshooting

### Port Already in Use

```
ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8080)
```

**Fix:**
```powershell
# Find what's using port 8080
netstat -ano | findstr :8080

# Use a different port
.\.venv\Scripts\python.exe -m uvicorn dashboard_server:app --port 8081
```

**Linux:**
```bash
lsof -i :8080
uvicorn dashboard_server:app --port 8081
```

---

### Authentication Errors (401 / 403)

```json
{"detail": "Invalid or missing API key"}
```

**Fix:**
1. Ensure `DASHBOARD_API_KEY` environment variable is set:
   ```powershell
   echo $env:DASHBOARD_API_KEY
   ```
2. Ensure your request includes the header:
   ```powershell
   curl -H "X-API-Key: your-secret-key-here" http://localhost:8080/api/metrics
   ```
3. Ensure the key in the header matches the environment variable exactly.

---

### Missing Metrics / Empty Dashboards

The server reads metrics from sibling repository evidence files. If metrics appear empty:

1. Ensure sibling repos are cloned in the same parent directory:
   ```powershell
   ls ..\ | Select-String "aws-agent-identity-guard|hf-model-provenance-scanner|adversarial-ml-lab"
   ```
2. Ensure those repos have `evidence/` directories with JSON metric files.
3. Check server logs for file-not-found warnings.

---

### Import Errors on Startup

```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix:**
```powershell
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn
```

---

### Server Crashes Immediately

Check Python version:
```powershell
py --version
# Needs 3.10+
```

Check for syntax errors:
```powershell
.\.venv\Scripts\python.exe -m py_compile dashboard_server.py
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `dashboard_server.py` | FastAPI server — serves static dashboards + metrics API |
| `index.html` | Main hub landing page |
| `shared/design-system.css` | Shared CSS for all dashboards |
| `shared/dashboard.js` | Shared JavaScript for dashboard interactivity |
| `*/index.html` | Per-product dashboard pages |
| `.github/workflows/` | CI configuration |

---

## Security Notes

- The `SECURITY_AUDIT.md` documents known vulnerabilities in this repo.
- The README notes this repo has critical security vulnerabilities per its own audit.
- **Do not expose this server to the public internet without additional hardening.**
