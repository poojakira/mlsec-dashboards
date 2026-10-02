# Claim Ledger — Poster 10 (10-mlsec-dashboards)

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

MIT • Python 3.12 • source snapshot bdb38ac • verified 2026-10-01. Classification: VERIFIED_AT_SNAPSHOT / VERIFIED_HISTORICAL / PARTIAL / UNVERIFIED / UNSUPPORTED.

| # | Claim | Classification | Evidence |
|---|---|---|---|
| 1 | Aggregates evidence from 8 active ML security repos | VERIFIED_AT_SNAPSHOT | README; dashboard_server.py discovers sibling evidence/*.json. |
| 2 | 36 test functions | VERIFIED_AT_SNAPSHOT | Counted `def test_` definitions in `tests/` at source snapshot bdb38ac; local verification records 36 passing pytest tests. |
| 3 | Shows weak results explicitly (OOD F1 0.72, ROC-AUC 0.54) | VERIFIED_AT_SNAPSHOT | README states weak-alongside-strong design; numbers sourced from sibling evidence files. |
| 4 | Token-authed REST API + static HTML | VERIFIED_AT_SNAPSHOT | README features; dashboard_server.py. |
| 5 | Live SOC monitoring / real-time alerting | UNSUPPORTED (disclaimed) | README: static evidence snapshots, not live monitoring. Not claimed. |

## Policy applied
- Only VERIFIED_AT_SNAPSHOT figures appear as prominent current results.
- Historical/projected values are labeled (dashed box / explicit note).
- Unsupported production/accuracy claims are omitted or shown in the red "NOT ESTABLISHED" box.
