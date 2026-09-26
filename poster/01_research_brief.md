# Research Brief — Poster 10

## Repository
`github.com/poojakira/mlsec-dashboards` (public, default branch `main`, primary language Python). MIT • Python 3.12 • HEAD 89a038a • verified 2026-09-26

## Academic Project Title
**Evidence-Centered Visualization for ML Security Engineering**

### Subtitle
Aggregating Repository-Level Measurements Into Traceable Technical Dashboards

## One-Sentence Contribution
An evidence-centered dashboard server that aggregates committed per-repo JSON into traceable HTML + a token-authed REST API, deliberately surfacing weak results (e.g. ROC-AUC 0.54, OOD F1 0.72) alongside strong ones rather than curating highlights.

## Problem Statement
Security dashboards often show curated highlights with no path back to the underlying measurement. A viewer cannot tell a real number from a hopeful one. This server reads committed JSON evidence from sibling repos and renders dashboards that show weak results next to strong ones, each traceable to its source file.

## Threat Model
Chain: UNTRACEABLE CLAIM -> EVIDENCE JSON -> FASTAPI AGGREGATOR -> REST + STATIC UI -> TRACEABLE DASHBOARD.
Adversary capability: n/a — transparency / integrity goal; Assumptions: evidence files committed; local aggregation; Out of scope: live SOC monitoring; real-time telemetry; alerting; Residual risk: static snapshot may lag current CI.

## Research / Engineering Question
> Can ML security claims be presented so each number traces back to a committed evidence file — including the weak results, not just the strong?

## Objective
Determine whether committed per-repo evidence can be aggregated into honest dashboards where every metric traces to its source artifact.

## Engineering Sub-Objectives
O1 — Discover sibling repo evidence
O2 — Per-project HTML dashboards
O3 — Token-authed aggregated REST API
O4 — Show weak results explicitly

## Methodology
1 Discover (repos) -> 2 Read (evidence) -> 3 Parse (JSON) -> 4 Render (HTML) -> 5 Serve (REST) -> 6·7 Auth (token)

## Current Verified Evidence + Claim Ledger
- **VERIFIED_CURRENT** — Aggregates evidence from 8 active ML security repos — README; dashboard_server.py discovers sibling evidence/*.json.
- **VERIFIED_CURRENT** — 27 test functions — Counted def test_ in tests/ (HEAD 89a038a).
- **VERIFIED_CURRENT** — Shows weak results explicitly (OOD F1 0.72, ROC-AUC 0.54) — README states weak-alongside-strong design; numbers sourced from sibling evidence files.
- **VERIFIED_CURRENT** — Token-authed REST API + static HTML — README features; dashboard_server.py.
- **UNSUPPORTED (disclaimed)** — Live SOC monitoring / real-time alerting — README: static evidence snapshots, not live monitoring. Not claimed.

## Important Negative / Honest Results
See RESULTS panel: Dashboards display weak results (OOD 0.72, ROC-AUC 0.54) next to strong ones — by design.

## Limitations
1. Static evidence snapshots, not live monitoring.
2. Data can lag the current CI state of each repo.
3. No alerting or real-time telemetry.
4. Depends on sibling repos committing evidence.
5. Local aggregation; not a hardened service.

## Future Work
• Scheduled evidence refresh from CI.
• Historical trend visualization.
• Signed-evidence verification on ingest.
• Diff view across commits.
• Per-metric provenance drill-down.

## Reproducibility
```
python dashboard_server.py
pytest tests/
```
Evidence: dashboard_server.py, sibling evidence/*.json, tests/

## References
[1] FastAPI docs · [2] OWASP ML Security · [3] MITRE ATLAS · [4] Reproducible research practice · [5] SLSA provenance · [6] NIST AI RMF 1.0
