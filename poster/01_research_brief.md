# Research Brief â€” Poster 10

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

## Repository
`github.com/poojakira/mlsec-dashboards` (public, default branch `main`, primary language Python). MIT â€¢ Python 3.12 â€¢ source snapshot a14ee69 â€¢ verified 2026-10-01

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
Adversary capability: n/a â€” transparency / integrity goal; Assumptions: evidence files committed; local aggregation; Out of scope: live SOC monitoring; real-time telemetry; alerting; Residual risk: static snapshot may lag current CI.

## Research / Engineering Question
> Can ML security claims be presented so each number traces back to a committed evidence file â€” including the weak results, not just the strong?

## Objective
Determine whether committed per-repo evidence can be aggregated into honest dashboards where every metric traces to its source artifact.

## Engineering Sub-Objectives
O1 â€” Discover sibling repo evidence
O2 â€” Per-project HTML dashboards
O3 â€” Token-authed aggregated REST API
O4 â€” Show weak results explicitly

## Methodology
1 Discover (repos) -> 2 Read (evidence) -> 3 Parse (JSON) -> 4 Render (HTML) -> 5 Serve (REST) -> 6 Auth (token)

## Evidence at Poster Snapshot + Claim Ledger
- **VERIFIED_AT_SNAPSHOT** â€” Aggregates evidence from 8 active ML security repos â€” README; dashboard_server.py discovers sibling evidence/*.json.
- **VERIFIED_AT_SNAPSHOT** â€” 37 test functions â€” Counted `def test_` definitions in `tests/` at source snapshot a14ee69; local verification records 37 passing pytest tests.
- **VERIFIED_AT_SNAPSHOT** â€” Shows weak results explicitly (OOD F1 0.72, ROC-AUC 0.54) â€” README states weak-alongside-strong design; numbers sourced from sibling evidence files.
- **VERIFIED_AT_SNAPSHOT** â€” Token-authed REST API + static HTML â€” README features; dashboard_server.py.
- **UNSUPPORTED (disclaimed)** â€” Live SOC monitoring / real-time alerting â€” README: static evidence snapshots, not live monitoring. Not claimed.

## Important Negative / Honest Results
See RESULTS panel: Dashboards display weak results (OOD 0.72, ROC-AUC 0.54) next to strong ones â€” by design.

## Limitations
1. Static evidence snapshots, not live monitoring.
2. Data can lag the current CI state of each repo.
3. No alerting or real-time telemetry.
4. Depends on sibling repos committing evidence.
5. Local aggregation; not a hardened service.

## Future Work
â€¢ Scheduled evidence refresh from CI.
â€¢ Historical trend visualization.
â€¢ Signed-evidence verification on ingest.
â€¢ Diff view across commits.
â€¢ Per-metric provenance drill-down.

## Reproducibility
```
python -m pytest tests/ -q
# Server startup requires an operator-supplied DASHBOARD_API_KEY.
```
Evidence: dashboard_server.py, sibling evidence/*.json, tests/

## References
[1] FastAPI docs Â· [2] OWASP ML Security Â· [3] MITRE ATLAS Â· [4] Reproducible research practice Â· [5] SLSA provenance Â· [6] NIST AI RMF 1.0
