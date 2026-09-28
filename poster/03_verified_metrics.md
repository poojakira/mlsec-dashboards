# Verified Metrics — Poster 10

> Evidence status: This is a dated repository snapshot at the commit identified below. `VERIFIED_AT_SNAPSHOT` means verified for that commit and environment; it does not assert the same result on the latest `main`. Compare newer claims with the repository evidence before reuse.

MIT • Python 3.12 • HEAD 30f729d • verified 2026-09-26. Verified for this poster on Windows / CPython 3.12.10.

## Headline cards
- 8 — REPOS AGGREGATED
- 27 — TEST FUNCTIONS
Notes: 8 active ML security repos' evidence aggregated. 27 test_ functions (HEAD 30f729d).

## Verified surface
| Item | Value |
|---|---|
| Dashboard framework | FastAPI |
| Auth on API | token |
| Design system | shared |

## Chart values
| Series | Value |
|---|---|
| Grouped F1 (redteam) | 97 |
| OOD F1 (redteam) | 72 |
| Weak ROC-AUC (poison) | 54 |
Note: Dashboards display weak results (OOD 0.72, ROC-AUC 0.54) next to strong ones — by design.

## Historical / provenance
Every displayed number is read from a committed evidence/*.json in a sibling repo — not hand-entered. Weak results are shown, not hidden.

## Not established by this repository
Live SOC monitoring. Real-time telemetry or alerting. That static snapshots equal current CI state.
