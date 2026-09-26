# Claim Ledger — Poster 10 (10-mlsec-dashboards)

MIT • Python 3.12 • HEAD 89a038a • verified 2026-09-26. Classification: VERIFIED_CURRENT / VERIFIED_HISTORICAL / PARTIAL / UNVERIFIED / UNSUPPORTED.

| # | Claim | Classification | Evidence |
|---|---|---|---|
| 1 | Aggregates evidence from 8 active ML security repos | VERIFIED_CURRENT | README; dashboard_server.py discovers sibling evidence/*.json. |
| 2 | 27 test functions | VERIFIED_CURRENT | Counted def test_ in tests/ (HEAD 89a038a). |
| 3 | Shows weak results explicitly (OOD F1 0.72, ROC-AUC 0.54) | VERIFIED_CURRENT | README states weak-alongside-strong design; numbers sourced from sibling evidence files. |
| 4 | Token-authed REST API + static HTML | VERIFIED_CURRENT | README features; dashboard_server.py. |
| 5 | Live SOC monitoring / real-time alerting | UNSUPPORTED (disclaimed) | README: static evidence snapshots, not live monitoring. Not claimed. |

## Policy applied
- Only VERIFIED_CURRENT figures appear as prominent current results.
- Historical/projected values are labeled (dashed box / explicit note).
- Unsupported production/accuracy claims are omitted or shown in the red "NOT ESTABLISHED" box.
