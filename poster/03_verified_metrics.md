# Verified Metrics — Poster 10

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

MIT • Python 3.12 • source snapshot c651768630530d2f8f2f4ff5f96ebd53e2c44142 • CI run 38298823655 on Python 3.12, initiated 2026-10-12 UTC.

## Headline cards
- 8 — DEFAULT REPOS CONFIGURED
- 37 — TEST FUNCTIONS
Notes: 8 default repositories configured; aggregation depends on available files. 37 `def test_` functions at source snapshot c651768630530d2f8f2f4ff5f96ebd53e2c44142; local verification records 37 passing pytest tests.

## Verified surface
| Item | Value |
|---|---|
| Dashboard framework | FastAPI |
| Auth on API | token |
| Design system | shared |

## Chart values
| Series | Value |
|---|---|
| Example grouped F1 (dimensionless) | 0.97 |
| Example OOD F1 (dimensionless) | 0.72 |
| Example ROC-AUC (dimensionless) | 0.54 |
Note: Dashboards display weak results (OOD 0.72, ROC-AUC 0.54) next to strong ones — by design.

## Historical / provenance
The server reads available recognized JSON metrics from configured sibling directories. Static authored dashboard examples are not all dynamically sourced. Example weak results are not new dashboard measurements.

## Not established by this repository
Live SOC monitoring. Real-time telemetry or alerting. That static snapshots equal cited CI state.


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.
