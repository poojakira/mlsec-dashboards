# mlsec-dashboards

**Maintainer:** Pooja Kiran ([@poojakira](https://github.com/poojakira))

FastAPI server that aggregates JSON evidence files from 8 active ML security repos into browsable dashboards with authenticated API endpoints.

---

## What This Does

Each of my ML security tools produces JSON output from benchmarks and test runs. This server collects those files from sibling repo directories, renders per-project HTML dashboards, and exposes REST endpoints for programmatic access.

The dashboards show actual numbers from committed evidence files. Weak results are shown alongside strong ones (e.g., ROC-AUC 0.54 on one attack type, F1 0.97 on grouped held-out templates and 0.7188 on novel-phrasing OOD data). The point is to have one URL where I can show someone what the tools report, with honest numbers and stated limitations.

---

## Features

- Discovers sibling repos and reads their `evidence/*.json` files
- Per-project HTML dashboards with a shared design system
- Aggregated metrics endpoint for CI integration
- Token-based authentication on API routes
- Shows gaps and weak results explicitly, not just highlights

---

## Architecture Overview

```
                         +-------------------+
                         |   Browser / CLI   |
                         +--------+----------+
                                  |
                    HTTP (localhost:8080)
                                  |
                         +--------v----------+
                         |   FastAPI Server   |
                         |  dashboard_server  |
                         |      .py          |
                         +---+----+-----+----+
                             |    |     |
              +--------------+    |     +--------------+
              |                   |                    |
     +--------v------+  +--------v------+  +----------v--------+
     | Static HTML   |  | /api/metrics  |  | /api/status       |
     | Dashboards    |  | (aggregated)  |  | (repo discovery)  |
     | (8 repos +    |  +--------+------+  +----------+--------+
     |  index.html)  |           |                    |
     +--------+------+           |                    |
              |            +-----v--------------------v-----+
              |            |  Sibling Repo Evidence Files    |
              |            |  (../repo-name/evidence/*.json) |
              |            +--------------------------------+
              |
     +--------v-----------+
     | shared/             |
     |  design-system.css  |
     |  dashboard.js       |
     +--------------------+
```

**Component Responsibilities:**

| Component | Responsibility |
|-----------|---------------|
| `dashboard_server.py` | FastAPI app: auth, CORS, evidence file discovery, metrics aggregation, static file serving |
| `index.html` | Main portfolio overview page with cards for the active repos, category filters, honesty notes |
| `shared/design-system.css` | Unified dark-theme design system (CSS custom properties, grid layouts, stat cards, tables) |
| `shared/dashboard.js` | Client-side utilities: animated counters, sortable/filterable tables, tab switching, live scan demo |
| `<repo-name>/index.html` | Per-project dashboard pages with embedded benchmark data |
| `tests/` | pytest suite covering auth, health, metrics extraction, JSON parsing |

---

## End-to-End Workflow

1. **Evidence generation**: Each sibling repo (e.g., `hf-model-provenance-scanner`) runs its benchmarks and writes JSON results to `evidence/`, `results/`, or `metrics/` directories.
2. **Server startup**: `dashboard_server.py` launches, mounts each `<repo-name>/` subdirectory as a static file route, and scans sibling directories for JSON evidence.
3. **Static dashboards**: Visiting `/mcp-agent-security-gateway/` serves that project's `index.html`, which imports the shared design system and renders pre-embedded benchmark data with animated counters and filterable tables.
4. **API aggregation**: `GET /api/metrics` (authenticated) walks all known sibling repos, reads their JSON evidence files, extracts standardized metric keys (fp_rate, detection_rate, f1, test_count, etc.), and returns aggregated summaries.
5. **Status discovery**: `GET /api/status` reports which sibling repos exist locally and how many evidence files each contains.
6. **Client rendering**: The shared `dashboard.js` handles intersection-observer-based counter animations, column sorting, category filtering, and tab switching without any framework dependency.

---

## Design Decisions and Trade-offs

**Static HTML with embedded data, not a SPA with API calls.**
The dashboards embed benchmark numbers directly in HTML. This means they work without a running server (open `index.html` in a browser), load instantly, and have zero JavaScript framework dependencies. The trade-off: updating numbers requires regenerating the HTML files.

**No database.**
Evidence lives as flat JSON files in sibling repos. The server reads them on demand. This avoids deployment complexity and keeps the source of truth in the repos that generate the data. The trade-off: every `/api/metrics` call scans the filesystem.

**Honest reporting over marketing.**
The index page explicitly states: "These are interactive evidence dashboards, not live security monitoring. Most data is static benchmark output embedded in HTML." Weak results (dataset-poisoning-detector at ROC-AUC 0.54, LLM redteam F1 0.9714 grouped vs 0.7188 novel-phrasing OOD) are shown as-is with explanations.

**Shared design system without build tools.**
One CSS file and one JS file, included via `<link>` and `<script>`. No bundler, no npm, no build step. This keeps the repo simple and makes individual dashboards self-contained. The trade-off: no tree-shaking, no TypeScript, no component framework.

**CORS restricted to localhost.**
The server is an internal development tool. CORS only allows `localhost:8080` and `localhost:3000`. This is intentional and documented.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI 0.141+, Uvicorn |
| Frontend | Vanilla HTML/CSS/JS, no framework |
| Design system | Custom CSS (dark theme, CSS custom properties) |
| Auth | API key via `X-API-Key` header, constant-time comparison (hmac) |
| Testing | pytest, httpx (via FastAPI TestClient) |
| Linting | Ruff |

### Installation

```bash
git clone https://github.com/poojakira/mlsec-dashboards.git
cd mlsec-dashboards

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### Quick Start

```bash
# Set the API key (required for /api/* endpoints)
export DASHBOARD_API_KEY="your-secret-key"

# Start the server
uvicorn dashboard_server:app --port 8080

# Or run directly:
python dashboard_server.py
```

Open `http://localhost:8080` for the main dashboard.

For a zero-server preview, open `index.html` directly in any browser.

### Usage Examples

```bash
# Health check (no auth required)
curl http://localhost:8080/health

# Get aggregated metrics across all sibling repos
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/api/metrics

# Check which repos have evidence files
curl -H "X-API-Key: $DASHBOARD_API_KEY" http://localhost:8080/api/status

# Run tests
pytest tests/ -v
```

---

## Security Considerations

- **Token-based authentication**: All `/api/*` endpoints require a valid `X-API-Key` header. Comparison uses `hmac.compare_digest` to prevent timing attacks.
- **Server misconfiguration protection**: If `DASHBOARD_API_KEY` is not set, the server returns HTTP 500 rather than silently allowing unauthenticated access.
- **No code execution**: The server never runs `subprocess`, `exec`, or `eval`. It only reads static JSON files from known directories.
- **File size limits**: Evidence files larger than 10 MB are skipped to prevent memory exhaustion.
- **CORS lockdown**: Only `localhost:8080` and `localhost:3000` origins are allowed. GET method only.
- **No secrets in the repo**: API keys come from environment variables.
- **Intended scope**: This is an authenticated internal developer tool. Public exposure would require an external identity-aware gateway/TLS layer and environment-specific rate limiting; direct unauthenticated internet exposure is unsupported.

---

## Evaluation Methods, Results, and Limitations

**How dashboards are evaluated:**
Each per-project dashboard reports metrics from that project's committed test suite or benchmark evidence. The source data is JSON evidence files generated by CI or local test runs.

**Key results shown across dashboards:**

| Project | Metric | Value | Context |
|---------|--------|-------|---------|
| MCP Security Gateway | Bundled self-test | 37/37 blocked (100%) | Fixed known-payload regression catalog; not a real-world detection rate |
| HF Provenance Scanner | Block rate | 100% (33/33) | Internal fixture suite |
| LLM Redteam Framework | F1 | 0.97 grouped | 0.7188 on novel-phrasing OOD benchmark |
| Adversarial ML Lab | Clean accuracy | 71.82% | Real SmallCNN benchmark; PGD-20 robust accuracy 0.00% at ε=8/255 |
| Model Privacy Attacks | MI AUC | 0.557 mean | Adult/OpenML, 5 seeds; 95% CI 0.5525–0.5615 |
| Dataset Poisoning Detector | ROC-AUC | ~0.54 | Near-baseline; target is 0.75 |
| ATT&CK v19 Core | v19 structure tests | 18/18 | Specific structure suite; not the repository's total test count |

**Limitations:**
- Most dashboard data is static benchmark output embedded in HTML, not live monitoring.
- Only the MCP gateway has real-time capability when its server is running.
- Metrics are from controlled benchmarks; real-world performance will differ.
- The `/api/metrics` endpoint only finds evidence if sibling repos are cloned locally.

---

## Intended-Use Readiness Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| Authentication | Done | API key with constant-time compare |
| Error handling | Done | JSON parse failures return None gracefully; missing repos reported; index.html read/decode errors return a clean fallback (no traceback); evidence files >10 MB skipped |
| Logging | Minimal | Uvicorn access logs only |
| Rate limiting | Not implemented | Acceptable for localhost use |
| HTTPS | Not included | Intended for local development |
| Monitoring/alerting | None | No health check integrations |
| CI/CD | Present | GitHub Actions directory exists |
| Test coverage | Good | 25 tests: auth, health, metrics extraction, JSON parsing, index-serving fallbacks, evidence size cap |
| Documentation | Good | README, RUNBOOK, SECURITY docs present |

**Verdict:** Suitable for its stated local developer-tool and portfolio-demo purpose. It is **not** presented as a production-facing service. Public deployment would require HTTPS, rate limiting, structured logging, stronger operational secret management, and deployment-specific security review.

---

## Roadmap / Future Improvements

- **Auto-refresh evidence**: Watch sibling repo directories for new JSON files and update metrics without server restart.
- **WebSocket push**: Push real-time updates to open dashboard pages when evidence changes.
- **Docker compose**: Single-command setup that clones sibling repos and starts the server.
- **Structured logging**: JSON logs with request IDs for debugging.
- **Evidence schema validation**: Validate incoming JSON against a defined schema rather than permissive key scanning.
- **Dashboard generation from evidence**: Auto-generate per-repo HTML pages from evidence files instead of hand-crafting each one.
- **HTTPS support**: Built-in TLS termination or reverse proxy configuration.
- **Expand beyond the current 8 active repos**: Make the dashboard list configurable rather than hardcoded.

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MITRE ATT&CK Framework v19](https://attack.mitre.org/)
- [OWASP ML Security Top 10](https://owasp.org/www-project-machine-learning-security-top-10/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [HuggingFace Model Security](https://huggingface.co/docs/hub/security)
- [Adversarial Robustness Toolbox](https://adversarial-robustness-toolbox.readthedocs.io/)

---

## Additional Documentation

- [INCIDENT_RUNBOOK.md](INCIDENT_RUNBOOK.md) - dashboard operational incident response

## License and Author

**License:** MIT

**Author:** Pooja Kiran  
- GitHub: [github.com/poojakira](https://github.com/poojakira)  
- LinkedIn: [linkedin.com/in/poojakiran](https://linkedin.com/in/poojakiran)

---

## Notes

Dashboard results are reported with their scope and limitations rather than as headline numbers: the 37/37 bundled self-test, for example, is labeled a fixed regression catalog rather than a real-world detection rate. The architecture is a flat file server with no database because the requirement is to make benchmark evidence browsable; a database or SPA front-end would add deployment complexity without changing that core function.
