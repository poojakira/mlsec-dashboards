# Claim Ledger — Poster 10 (10-mlsec-dashboards)

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

MIT • Python 3.12 • source snapshot c651768630530d2f8f2f4ff5f96ebd53e2c44142 • verified 2026-10-12. Classification: VERIFIED_AT_SNAPSHOT / VERIFIED_HISTORICAL / PARTIAL / UNVERIFIED / UNSUPPORTED.

| # | Claim | Classification | Evidence |
|---|---|---|---|
| 1 | Configures 8 default sibling repositories, with aggregation dependent on available evidence | VERIFIED_AT_SNAPSHOT | README; dashboard_server.py discovers sibling evidence/*.json. |
| 2 | 37 test functions | VERIFIED_AT_SNAPSHOT | Counted `def test_` definitions in `tests/` at source snapshot c651768630530d2f8f2f4ff5f96ebd53e2c44142; local verification records 37 passing pytest tests. |
| 3 | Shows weak results explicitly (OOD F1 0.72, ROC-AUC 0.54) | VERIFIED_AT_SNAPSHOT | README states weak-alongside-strong design; these are cited sibling example values; static HTML examples are not all dynamically sourced. |
| 4 | Token-authed REST API + static HTML | VERIFIED_AT_SNAPSHOT | README features; dashboard_server.py. |
| 5 | Live SOC monitoring / real-time alerting | UNSUPPORTED (disclaimed) | README: static evidence snapshots, not live monitoring. Not claimed. |

## Policy applied
- Only VERIFIED_AT_SNAPSHOT figures appear as prominent current results.
- Historical/projected values are labeled (dashed box / explicit note).
- Unsupported production/accuracy claims are omitted or shown in the red "NOT ESTABLISHED" box.


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.
